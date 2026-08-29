# URAI Ransomware Resilience — Repository Map

**Status:** Stage 0 repository map  
**Scope:** Energy & Petrochemical Ransomware Resilience Synthetic PoC  
**Safety classification:** Defensive synthetic PoC; recommendation/review only

## 1. Purpose

This document records the repository directories that currently exist and
clearly distinguishes planned future directories from the implemented
Stage 0 foundation.

Only directories confirmed to exist in the repository are marked as
implemented.

Future directories are explicitly marked PLANNED and are not required to be
implemented during Stage 0.

---

## 2. Current Stage 0 Repository Structure

```text
urai_ransomeware_resilience/
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── audit/
│       │   ├── controllers/
│       │   ├── policies/
│       │   ├── routes/
│       │   ├── schemas/
│       │   └── services/
│       └── tests/
├── docs/
│   └── ransomware/
├── requirements.txt
├── verify_environment.py
└── README.md

The following are generated runtime/cache directories and are not considered
application architecture:

.pytest_cache/
__pycache__/


## 3. Implemented Stage 0 Backend

Root: apps/backend/app/

The following directories currently exist:

Directory	Status	Purpose
apps/backend/app/routes/	IMPLEMENTED	API route boundary
apps/backend/app/controllers/	IMPLEMENTED	Request/control orchestration boundary
apps/backend/app/services/	IMPLEMENTED	Backend service logic and safe synthetic responses
apps/backend/app/schemas/	IMPLEMENTED	Request, response, enum and contract schemas
apps/backend/app/policies/	IMPLEMENTED	Safety and policy enforcement boundary
apps/backend/app/audit/	IMPLEMENTED	Audit context boundary

## 4. Tests

Root: `tests/backend/tests/`

Status: IMPLEMENTED

The test suite verifies API behavior, schema validation, decision states,
provenance values and safety requirements.

## 5. Documentation

Root: docs/ransomware/

Status: IMPLEMENTED

Current documentation includes:

Repository map
Safety policy
Planned internal module boundaries
Stage 0 task tracker
Frozen API contract
## 6. Planned Future Directories

The following directories are architectural targets for later stages and are
not currently implemented unless explicitly stated elsewhere.

Directory	Status	Planned Purpose
apps/frontend/	PLANNED	Dashboard and frontend presentation
apps/ml-services/	PLANNED	Internal ML-service boundary and inference components
data/synthetic/ransomware_poc/	PLANNED	Synthetic scenarios, telemetry and ground truth
apps/ml-services/config/ransomware/	PLANNED	Governed ML and scenario configuration
artifacts/	PLANNED	Versioned model, calibration and evaluation artifacts

These planned directories must not be represented as implemented Stage 0
components.

## 7. Stage 0 Boundary

Stage 0 establishes repository readiness, safety restrictions, API contracts,
environment reproducibility and test controls.

The following remain outside the Stage 0 implementation boundary:

Dataset generation
Feature engineering
Model training
Model calibration
ML inference implementation
Frontend dashboard implementation
Production telemetry integration
Operational response integration

No placeholder decision logic is created for these future components.

## 8. Safety Boundary

The repository contains only defensive synthetic PoC functionality.

The project must not:

Execute ransomware
Execute encryption payloads
Perform destructive behavior
Detonate malware
Perform active probing
Execute containment actions
Execute recovery actions
Execute operational control actions

Recommendations remain non-executing and require human approval.

`real_action_executed` remains `false`.

## 9. Source of Truth

This repository map must reflect the actual repository state.

When a future module is introduced, its directory status should be changed
from PLANNED to IMPLEMENTED only after the directory and its corresponding
controlled implementation are actually present.