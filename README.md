# DrugRiskEngine

Clinical Decision Support (CDS) system that detects drug-condition interactions in synthetic patient records.

## Overview

DrugRiskEngine pulls patient data from a HAPI FHIR server (generated via Synthea), cross-references active diagnoses and medications against a SQLite knowledge base of 32 drug-condition interaction rules, and surfaces clinical alerts with severity ratings.

## Components

| Component | Description |
|-----------|-------------|
| `inject_and_upload.py` | Injects synthetic drug-condition traps into Synthea output and uploads to FHIR |
| `extract_patients.py` | CLI-based alert engine that scans patients and prints interactions |
| `app.py` | FastAPI server exposing `/patients` and `/alerts/{patient_id}` endpoints |
| `index.html` | Clinical portal frontend with patient directory, alert cards, EN/FR toggle |
| `setup_real_rules.py` | Seeds `clinical_knowledge.db` with 32 interaction rules across 11 categories |
| `test_engine.py` | Pytest suite (8 tests) for the alert matching logic |

## Quick Start

```bash
# 1. Start HAPI FHIR
docker start hapi-fhir-server

# 2. Seed the clinical rules database
python setup_real_rules.py

# 3. Start the API server
uvicorn app:app --host 0.0.0.0 --port 8000

# 4. Open the portal
open http://localhost:8000/static/
```

## API

- `GET /patients` — list all patients (id, name, gender, birthDate)
- `GET /alerts/{patient_id}` — active diagnoses, medications, and triggered alerts with severity and justifications

## Data Sources

- **Synthea** generates synthetic patient FHIR bundles
- **HAPI FHIR** serves as the patient data repository
- **NIH RxNorm API** resolves drug codes to generic names (cached in memory)
- **SQLite** stores clinical interaction rules and audit logs

## License

MIT
