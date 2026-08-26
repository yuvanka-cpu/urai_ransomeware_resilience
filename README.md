# URAI Energy & Petrochemical Ransomware Resilience

## Overview

This repository contains the Stage 0 backend foundation for the URAI Energy & Petrochemical Ransomware Resilience Proof of Concept.

The PoC is synthetic and defensive. It provides structured ransomware-resilience responses for review and recommendation purposes only.

No real ransomware, destructive actions, operational containment, or recovery execution is implemented.

## Stage 0 Scope

Stage 0 focuses on:

- FastAPI backend foundation
- Health-check endpoint
- Pydantic request and response schemas
- Fixed decision, incident-stage, and severity enums
- Safety-field enforcement
- Synthetic mocked response states
- API contract tests
- Health-check tests
- Schema-validation tests
- Documentation

## Mock Response States

The backend provides five Stage 0 mock states:

- Normal
- Investigate
- High Risk
- Unavailable
- Fallback

These are synthetic fixtures used to validate the API contract. They do not represent live ML output.

## Safety Controls

Every ransomware-resilience response requires:

- `human_approval_required = true`
- `real_action_executed = false`

The PoC does not execute:

- ransomware
- encryption
- host isolation
- account disabling
- firewall changes
- controller/DCS/SIS actions
- recovery actions
- other destructive or operational containment actions

## Backend Structure

```text
apps/backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── ransomware.py
│   ├── services/
│   │   └── ransomware_mock.py
│   └── schemas/
│       ├── enums.py
│       ├── requests.py
│       └── responses.py
└── tests/
    ├── test_api.py
    ├── test_health.py
    └── test_schemas.py

## Setup and Run

From the repository root:

cd apps/backend
python -m pip install -r ../../requirements.txt
uvicorn app.main:app --reload

The API will be available at:
http://127.0.0.1:8000

Health check:
GET /health

Expected response:
{"status":"ok"}

## Sample Request

The Stage 0 request contract includes:
{
  "schema_version": "1.0",
  "use_case": "ransomware_resilience",
  "industry": "energy",
  "site_id": "synthetic-site-001",
  "site_type": "control_centre",
  "scenario_id": "rw-stage0-normal",
  "observable_input": {}
}
The values shown above are synthetic Stage 0 implementation fixtures and are not live operational data.

## Sample Response States

Stage 0 provides synthetic fixtures for:

Normal
Investigate
High Risk
Unavailable
Fallback

All responses enforce:
human_approval_required = true
real_action_executed = false

Unavailable response
{
  "decision": "unavailable",
  "data_provenance": "UNAVAILABLE",
  "runtime_state": "unavailable",
  "human_approval_required": true,
  "real_action_executed": false,
  "warnings": ["Synthetic runtime failure: response unavailable."]
}

Fallback response
{
  "decision": "investigate",
  "data_provenance": "FALLBACK",
  "runtime_state": "fallback",
  "human_approval_required": true,
  "real_action_executed": false,
  "warnings": ["FALLBACK: live-model output is unavailable."]
}
Fallback output must not be presented as live-model success.

The complete response contract is defined in:
apps/backend/app/schemas/responses.py

## Provenance

The response contract includes:

request IDs
trace IDs
artifact provenance
data provenance
warnings

Synthetic and fallback outputs must remain clearly distinguishable from live-model output.

## Testing

From apps/backend:

pytest -v

## Stage 0 Boundary

Stage 0 includes:

schema-validation tests
health-check tests
API-contract tests
Stage 0 Boundary

Stage 0 does not include:

ML integration
real ransomware execution
encryption
destructive activity
operational containment
recovery execution
automated operational actions
commands to operational systems

The system must never represent a recommendation as an executed action.
