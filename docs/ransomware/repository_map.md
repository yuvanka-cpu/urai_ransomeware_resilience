# URAI Ransomware Resilience — Repository Map

**Status:** Stage 0 corrected repository map
**Scope:** Energy & Petrochemical Ransomware Resilience Synthetic PoC
**Safety classification:** Defensive synthetic PoC; recommendation/review only

## Purpose

This map distinguishes implemented Stage 0 components from retained directory skeletons and planned later-stage work. A directory is not described as implemented merely because a README keeps it in source control.

## Verified repository structure

```text
urai_ransomeware_resilience/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── audit/          # skeleton only
│   │   │   ├── controllers/    # skeleton only
│   │   │   ├── policies/       # skeleton only
│   │   │   ├── routes/         # implemented Stage 0 mock API
│   │   │   ├── schemas/        # implemented Stage 0 contracts
│   │   │   └── services/       # implemented Stage 0 fixtures
│   │   ├── tests/              # implemented Stage 0 tests
│   │   ├── pytest.ini
│   │   └── verify_environment.py
│   ├── frontend/               # planned skeleton
│   └── ml-services/            # planned skeleton
│       └── config/ransomware/  # planned configuration skeleton
├── artifacts/                  # planned governed-artifact skeleton
├── data/synthetic/ransomware_poc/ # planned Stage 4 data root
├── docs/ransomware/            # active documentation
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── requirements.lock
├── requirements.lock.sha256
└── requirements.txt
```

Generated `.pytest_cache/` and `__pycache__/` directories are excluded from application architecture and delivery packages.

## Current status

| Path | Status | Purpose |
|---|---|---|
| `apps/backend/app/routes/` | Implemented Stage 0 | Health-adjacent mock API boundary |
| `apps/backend/app/schemas/` | Implemented Stage 0 | Request, response and controlled enum schemas |
| `apps/backend/app/services/` | Implemented Stage 0 fixture | Safe synthetic contract fixtures only |
| `apps/backend/tests/` | Implemented Stage 0 | API, health, safety and schema tests |
| `apps/backend/app/controllers/` | Skeleton | Later request orchestration |
| `apps/backend/app/policies/` | Skeleton | Later policy enforcement |
| `apps/backend/app/audit/` | Skeleton | Later audit context |
| `apps/frontend/` | Planned skeleton | Dashboard implementation in later stages |
| `apps/ml-services/` | Planned skeleton | Deterministic and ML runtime in later stages |
| `apps/ml-services/config/ransomware/` | Planned skeleton | Stage 1–3 governed configuration |
| `data/synthetic/ransomware_poc/` | Planned skeleton | Synthetic dataset generation from Stage 4 |
| `artifacts/` | Planned skeleton | Versioned checksummed artifacts |
| `docs/ransomware/` | Active | Contracts, safety, tracking and review evidence |

## Stage 0 boundary

Stage 0 establishes repository readiness, safety restrictions, the decision/provenance/safety sub-contract, dependency reproducibility and test controls. It does not include dataset generation, feature engineering, model training, ML inference, dashboard implementation or operational integrations.

The five backend mock responses are explicitly contract fixtures. They are not model output and must never be presented as live inference.

## Safety boundary

No component executes ransomware, encryption, destructive behavior, active probing, account disabling, containment, recovery, startup or operational-control actions. Recommendations remain non-executing, `human_approval_required` remains `true`, and `real_action_executed` remains `false`.

## Maintenance rule

Update this map whenever a directory changes state. Change `Skeleton` or `Planned` to `Implemented` only after controlled implementation and its tests are present.
