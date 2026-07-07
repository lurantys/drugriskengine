import json, os, requests, glob, uuid

FHIR_SERVER = "http://localhost:8080/fhir"
SYNTHEA_DIR = os.path.join(os.path.dirname(__file__), "synthea-output", "fhir")

TRAPS = [
    {"condition": "Pregnancy", "condition_code": "77386006", "medication": "Ibuprofen", "rxnorm": "5640"},
    {"condition": "Asthma", "condition_code": "195967001", "medication": "Propranolol", "rxnorm": "8745"},
    {"condition": "Chronic Kidney Disease", "condition_code": "723190009", "medication": "Spironolactone", "rxnorm": "114488"},
    {"condition": "Diabetes", "condition_code": "73211009", "medication": "Pseudoephedrine", "rxnorm": "8896"},
    {"condition": "Heart Failure", "condition_code": "84114007", "medication": "Ibuprofen", "rxnorm": "5640"},
]

files = sorted([f for f in os.listdir(SYNTHEA_DIR) if f.endswith(".json") and not f.startswith("hospital") and not f.startswith("practitioner")])
first_5 = files[:5]

for i, fname in enumerate(first_5):
    fpath = os.path.join(SYNTHEA_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    trap = TRAPS[i]
    patient_id = None
    for entry in bundle.get("entry", []):
        if entry["resource"]["resourceType"] == "Patient":
            patient_id = entry["resource"]["id"]
            patient_fullurl = entry["fullUrl"]
            break

    if not patient_id:
        print(f"SKIP {fname}: no Patient found")
        continue

    patient_ref = patient_fullurl if patient_fullurl else f"urn:uuid:{patient_id}"

    condition_id = str(uuid.uuid4())
    condition_entry = {
        "fullUrl": f"urn:uuid:{condition_id}",
        "resource": {
            "resourceType": "Condition",
            "id": condition_id,
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": trap["condition_code"], "display": trap["condition"]}]},
            "subject": {"reference": patient_ref}
        },
        "request": {"method": "POST", "url": "Condition"}
    }

    med_id = str(uuid.uuid4())
    med_entry = {
        "fullUrl": f"urn:uuid:{med_id}",
        "resource": {
            "resourceType": "MedicationRequest",
            "id": med_id,
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": trap["rxnorm"], "display": trap["medication"]}]},
            "subject": {"reference": patient_ref}
        },
        "request": {"method": "POST", "url": "MedicationRequest"}
    }

    bundle["entry"].append(condition_entry)
    bundle["entry"].append(med_entry)

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(f"INJECTED [{i+1}/5] {fname}: {trap['condition']} + {trap['medication']} (RxNorm {trap['rxnorm']})")

print("\n--- Uploading all 20 patients to FHIR server ---")
for fname in files:
    fpath = os.path.join(SYNTHEA_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    resp = requests.post(f"{FHIR_SERVER}", json=bundle, headers={"Content-Type": "application/fhir+json"})
    print(f"  {fname}: HTTP {resp.status_code}")

print("\nDone.")
