# URAI Ransomware Resilience — Repository Map

## Purpose

This repository contains a synthetic, defensive Proof of Concept for
Energy & Petrochemical Ransomware Resilience.

Stage 0 establishes the repository foundation, safety boundaries, API
contracts, synthetic response states, validation, and test controls.

## Confirmed Current Structure

```text
urai_ransomeware_resilience/
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── main.py                    [CURRENT]
│       │   ├── config.py                  [CURRENT]
│       │   ├── routes/
│       │   │   └── ransomware.py           [CURRENT]
│       │   ├── services/
│       │   │   └── ransomware_mock.py      [CURRENT]
│       │   ├── schemas/
│       │   │   ├── enums.py                [CURRENT]
│       │   │   ├── requests.py             [CURRENT]
│       │   │   └── responses.py            [CURRENT]
│       │   ├── controllers/                [PLANNED]
│       │   ├── policies/                   [PLANNED]
│       │   └── audit/                      [PLANNED]
│       ├── tests/
│       │   ├── test_api.py                 [CURRENT]
│       │   ├── test_health.py              [CURRENT]
│       │   └── test_schemas.py             [CURRENT]
│       └── pytest.ini                      [CURRENT]
├── docs/
│   └── ransomware/
│       ├── repository_map.md               [CURRENT]
│       └── safety_policy.md                [CURRENT]
├── .env.example                            [CURRENT]
├── .gitignore                              [CURRENT]
├── README.md                               [CURRENT]
└── requirements.txt                        [CURRENT]

##Planned Module Boundaries

The following components are planned for later implementation and are not considered implemented during Stage 0.

apps/backend/app/controllers/
Backend orchestration and request-flow coordination.
apps/backend/app/policies/
Safety, recommendation, fallback, and policy enforcement logic.
apps/backend/app/audit/
Structured audit events, request correlation, provenance, and review state.
apps/ml/
Planned internal ML service boundary for model inference.
apps/frontend/
Planned browser-facing dashboard and typed views.
data/synthetic/
Planned synthetic telemetry, ground-truth, faulty-data, and scenario fixtures.
artifacts/
Planned versioned model, dataset, manifest, checksum, and evaluation artifacts.

These planned components must not be treated as implemented Stage 0 functionality.

##Stage 0 Implementation Boundary

Implemented Stage 0 functionality is limited to:

FastAPI backend foundation
request and response API schemas
decision, incident-stage, and severity enums
safe synthetic response states
health checking
schema/API tests
safety documentation
repository documentation

ML inference, dataset generation, model development, frontend implementation, operational containment, and recovery execution are outside the Stage 0 implementation boundary.
