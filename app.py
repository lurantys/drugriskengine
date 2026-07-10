import sqlite3, datetime, asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

FHIR_SERVER = "http://localhost:8080/fhir"
DB_PATH = "clinical_knowledge.db"
AUDIT_PATH = "alerts_audit.db"
DRUG_NAME_CACHE = {}
RXNORM_API = "https://rxnav.nlm.nih.gov/REST/rxcui"

async def resolve_drug_name(code: str) -> str:
    if code in DRUG_NAME_CACHE:
        return DRUG_NAME_CACHE[code]
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"{RXNORM_API}/{code}/property.json?propName=RxNorm%20Name")
        if r.status_code == 200:
            concepts = r.json().get("propConceptGroup", {}).get("propConcept", [])
            if concepts:
                name = concepts[0].get("propValue", "")
                if name:
                    DRUG_NAME_CACHE[code] = name
                    return name
    except Exception:
        pass
    DRUG_NAME_CACHE[code] = f"RxNorm {code}"
    return f"RxNorm {code}"

app = FastAPI(title="CDS Alert Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=".", html=True), name="static")

def init_audit():
    conn = sqlite3.connect(AUDIT_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            detected_condition TEXT NOT NULL,
            offending_rxnorm TEXT NOT NULL,
            severity TEXT NOT NULL,
            justification TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_alert(patient_id, condition, rxnorm, severity, justification):
    conn = sqlite3.connect(AUDIT_PATH)
    conn.execute(
        "INSERT INTO alerts (timestamp, patient_id, detected_condition, offending_rxnorm, severity, justification) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.datetime.utcnow().isoformat() + "Z", patient_id, condition, rxnorm, severity, justification)
    )
    conn.commit()
    conn.close()

def match_rules(condition_name, rxnorm_code):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT condition_keyword, medication_name, severity, justification FROM clinical_rules WHERE rxnorm_code = ?",
        (rxnorm_code,)
    )
    matched = []
    for row in cur.fetchall():
        keyword = row[0].lower()
        if keyword in condition_name.lower():
            matched.append({
                "condition_keyword": row[0],
                "medication_name": row[1],
                "severity": row[2],
                "justification": row[3]
            })
    conn.close()
    return matched

init_audit()

@app.get("/patients")
async def get_patients():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{FHIR_SERVER}/Patient?_count=50",
            headers={"Accept": "application/fhir+json"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="FHIR server error")
    data = resp.json()
    patients = []
    for entry in data.get("entry", []):
        r = entry["resource"]
        pid = r.get("id", "")
        name = r.get("name", [{}])[0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        full_name = f"{given} {family}".strip() or pid
        gender = r.get("gender", "")
        birth_date = r.get("birthDate", "")
        patients.append({"id": pid, "name": full_name, "gender": gender, "birth_date": birth_date})
    return patients

@app.get("/alerts/{patient_id}")
async def get_alerts(patient_id: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        cond_resp = await client.get(
            f"{FHIR_SERVER}/Condition?subject=Patient/{patient_id}&_count=1000",
            headers={"Accept": "application/fhir+json"}
        )
        med_resp = await client.get(
            f"{FHIR_SERVER}/MedicationRequest?subject=Patient/{patient_id}&_count=1000",
            headers={"Accept": "application/fhir+json"}
        )

    if cond_resp.status_code != 200 or med_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="FHIR server error")

    cond_data = cond_resp.json()
    med_data = med_resp.json()

    conditions = set()
    for entry in cond_data.get("entry", []):
        r = entry["resource"]
        status = r.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
        if status and status != "active":
            continue
        display = r.get("code", {}).get("coding", [{}])[0].get("display", "")
        if display:
            conditions.add(display)

    seen_codes = set()
    raw_codes = []
    for entry in med_data.get("entry", []):
        r = entry["resource"]
        if r.get("status") != "active":
            continue
        for c in r.get("medicationCodeableConcept", {}).get("coding", []):
            code = c.get("code", "")
            if code and code not in seen_codes:
                seen_codes.add(code)
                raw_codes.append(code)

    resolved = await asyncio.gather(*[resolve_drug_name(c) for c in raw_codes])
    medications = [{"code": c, "name": n} for c, n in zip(raw_codes, resolved)]

    alerts = []
    seen = set()
    for cond_display in conditions:
        for med in medications:
            rxnorm = med["code"]
            matches = match_rules(cond_display, rxnorm)
            for m in matches:
                key = (cond_display, rxnorm)
                if key in seen:
                    continue
                seen.add(key)
                alert = {
                    "patient_id": patient_id,
                    "condition": cond_display,
                    "rxnorm": rxnorm,
                    "matched_keyword": m["condition_keyword"],
                    "medication_name": m["medication_name"],
                    "severity": m["severity"],
                    "justification": m["justification"]
                }
                alerts.append(alert)
                log_alert(patient_id, cond_display, rxnorm, m["severity"], m["justification"])

    return {"patient_id": patient_id, "conditions": list(conditions), "medications": medications, "alerts": alerts, "alert_count": len(alerts)}
