import requests, json

FHIR_SERVER = "http://localhost:8080/fhir"

RISK_RULES = [
    {"condition": "Pregnancy", "condition_code": "77386006", "medication": "Ibuprofen", "rxnorm": "5640", "severity": "HIGH", "description": "NSAIDs like Ibuprofen are contraindicated in pregnancy (risk of premature closure of ductus arteriosus)"},
    {"condition": "Asthma", "condition_code": "195967001", "medication": "Propranolol", "rxnorm": "8745", "severity": "HIGH", "description": "Beta-blockers like Propranolol can worsen bronchospasm in asthma patients"},
    {"condition": "Chronic Kidney Disease", "condition_code": "723190009", "medication": "Spironolactone", "rxnorm": "114488", "severity": "HIGH", "description": "Spironolactone increases hyperkalemia risk in CKD patients"},
    {"condition": "Diabetes", "condition_code": "73211009", "medication": "Pseudoephedrine", "rxnorm": "8896", "severity": "MODERATE", "description": "Pseudoephedrine can cause hyperglycemia and interfere with diabetes control"},
    {"condition": "Heart Failure", "condition_code": "84114007", "medication": "Ibuprofen", "rxnorm": "5640", "severity": "HIGH", "description": "NSAIDs like Ibuprofen can worsen heart failure by causing fluid retention"},
]

def fetch_all(base_url):
    resources = []
    url = base_url
    while url:
        resp = requests.get(url, headers={"Accept": "application/fhir+json"}, timeout=30)
        data = resp.json()
        resources.extend(data.get("entry", []))
        next_link = [l for l in data.get("link", []) if l.get("relation") == "next"]
        url = next_link[0]["url"] if next_link else None
    return resources

def get_patient_name(patient_ref):
    parts = patient_ref.split("/")
    pid = parts[-1]
    resp = requests.get(f"{FHIR_SERVER}/Patient/{pid}", headers={"Accept": "application/fhir+json"}, timeout=15)
    if resp.status_code != 200:
        return pid
    pt = resp.json()
    name = pt.get("name", [{}])[0]
    given = " ".join(name.get("given", []))
    family = name.get("family", "")
    return f"{given} {family}".strip() or pid

def main():
    print("=" * 80)
    print("  CLINICAL DECISION SUPPORT (CDS) — DRUG-CONDITION CONFLICT DETECTION ENGINE")
    print("=" * 80)

    med_entries = fetch_all(f"{FHIR_SERVER}/MedicationRequest?_include=MedicationRequest:patient")
    cond_entries = fetch_all(f"{FHIR_SERVER}/Condition")

    patient_conditions = {}
    for entry in cond_entries:
        r = entry["resource"]
        subj = r.get("subject", {}).get("reference", "")
        if not subj:
            continue
        clinical_status = r.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
        if clinical_status and clinical_status != "active":
            continue
        code = r.get("code", {}).get("coding", [{}])[0].get("code", "")
        display = r.get("code", {}).get("coding", [{}])[0].get("display", "")
        pid = subj.split("/")[-1]
        patient_conditions.setdefault(pid, []).append({"code": code, "display": display})

    patient_medications = {}
    for entry in med_entries:
        r = entry.get("resource", {})
        if r.get("resourceType") != "MedicationRequest":
            continue
        subj = r.get("subject", {}).get("reference", "")
        if not subj:
            continue
        status = r.get("status", "")
        if status != "active":
            continue
        coding = r.get("medicationCodeableConcept", {}).get("coding", [])
        for c in coding:
            rxnorm = c.get("code", "")
            display = c.get("display", "")
            pid = subj.split("/")[-1]
            patient_medications.setdefault(pid, set()).add((rxnorm, display))

    alerts_found = 0
    for pid, conditions in patient_conditions.items():
        for cond in conditions:
            for rule in RISK_RULES:
                if cond["code"] != rule["condition_code"]:
                    continue
                meds = patient_medications.get(pid, set())
                for rxnorm, med_display in meds:
                    if rxnorm != rule["rxnorm"]:
                        continue
                    alerts_found += 1
                    pname = get_patient_name(f"Patient/{pid}")
                    print()
                    print("!" * 80)
                    print(f"  ALERT #{alerts_found} — DRUG-CONDITION CONFLICT DETECTED")
                    print("!" * 80)
                    print(f"  Patient       : {pname} (ID: {pid})")
                    print(f"  Condition     : {cond['display']} (SNOMED: {cond['code']})")
                    print(f"  Medication    : {med_display} (RxNorm: {rxnorm})")
                    print(f"  Severity      : {rule['severity']}")
                    print(f"  Description   : {rule['description']}")
                    print("-" * 80)

    if alerts_found == 0:
        print("\n  No drug-condition conflicts detected.")
    else:
        print(f"\n  Total alerts: {alerts_found}")

if __name__ == "__main__":
    main()
