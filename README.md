# URAI Energy & Petrochemical Ransomware Resilience

This repository contains the verified Stage 0 foundation and a Stage 1 review package for a synthetic, defensive ransomware-resilience proof of concept. It is a separate repository; the FDI dashboard is a process and governance reference, not a code dependency.

## Safety boundary

The project represents harmless observable ransomware-effect telemetry and review recommendations. It does not execute malware, encryption, destructive operations, active probing, isolation, account changes, firewall changes, restore/startup actions or commands to DCS, SIS, PLC, relay or other operational systems.

Every response enforces:

```text
human_approval_required = true
real_action_executed = false
```

## Stage 0 implementation

- FastAPI backend foundation and health endpoint
- Versioned request/response schemas and controlled enums
- Recursive synthetic-truth leakage rejection
- Fixed safety fields and bounded confidence/resilience values
- Five explicitly synthetic contract fixtures: normal, investigate, high risk, fallback and unavailable
- Reproducible dependency lock and verification command
- API, health, safety and negative schema tests
- Separate planned roots for frontend, ML service, configuration, synthetic data and governed artifacts

The Stage 1 review package adds ten sector-specific use-case contracts, controlled asset states, safe recommendation templates, cyber/operational separation and measurable acceptance gates. Dataset generation, model development, frontend implementation and operational integrations are not included.

## Repository structure

```text
apps/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── controllers/  # skeleton
│   │   ├── policies/     # skeleton
│   │   └── audit/        # skeleton
│   └── tests/
├── frontend/             # planned skeleton
└── ml-services/          # planned skeleton
    └── config/ransomware/
artifacts/                # planned skeleton
data/synthetic/ransomware_poc/ # planned Stage 4 data root
docs/ransomware/
```

## Setup and verification

Use Python 3.12.x. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
cd apps\backend
..\..\.venv\Scripts\python.exe verify_environment.py
..\..\.venv\Scripts\python.exe -m pytest -q
```

Expected verification result (the exact test count may increase as later-stage contracts are added):

```text
Environment verification: PASS
all tests passed
```

One unsuppressed upstream TestClient deprecation warning is documented in `docs/ransomware/known_warnings.md`.

## Run the backend

From `apps/backend`:

```powershell
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. The health endpoint is `GET /health` and must return:

```json
{"status": "ok"}
```

The `/mock/*` endpoints are Stage 0 contract fixtures only. They are never live-model output.

## Stage progression

Stage 0 is independently verified and closed at commit `fe9a3f98d78cdf30485445cf93b9fac49789d5fd`. Stage 1 is in review until its ten use-case contracts, safety language and acceptance gates receive contributor/domain approval and a clean-clone verification. Synthetic dataset generation begins at Stage 4 only after Stage 2 ontology/graphs and Stage 3 canonical schemas also pass their exit gates.
