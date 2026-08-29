# URAI Ransomware Resilience — Stage 0 Task Tracker

**Stage:** Stage 0 — Repository Readiness, Boundaries and Execution Controls  
**Source:** URAI Ransomware Resilience Module Detailed Execution Task Sheet  
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Stage 0 Objective

Establish the working repository, safe operating boundary, reproducible
environment and task-control method before any dataset or model code is
written.

## Task Tracker

| Tracker ID | Source Task | Requirement | Status | Completion Evidence |
|---|---|---|---|---|
| RW-0001 | RW-000 Task 1 | Confirm active frontend, backend and ML-service roots and document existing/planned paths. | DN | `docs/ransomware/repository_map.md` |
| RW-0002 | RW-000 Task 2 | Create the ransomware module directory skeleton for configuration, synthetic data, tests, artifacts, documentation and application code without placeholder decisions. | DN | Repository structure; `docs/ransomware/repository_map.md`; application foundation |
| RW-0003 | RW-000 Task 3 | Define and version the PoC safety policy covering synthetic-only telemetry and prohibition of malware, encryption, detonation, active probing and operational actions. | DN | `docs/ransomware/safety_policy.md`; safety/API tests |
| RW-0004 | RW-000 Task 4 | Define decision states `normal`, `investigate`, `high_risk`, and `unavailable`; enforce `human_approval_required=true` and `real_action_executed=false`. | DN | `app/schemas/enums.py`; `app/schemas/responses.py`; API/schema tests |
| RW-0005 | RW-000 Task 5 | Define controlled provenance values: `LIVE_MODEL`, `SYNTHETIC_GROUND_TRUTH`, `STATIC_SCENARIO_METADATA`, `DERIVED_BY_BACKEND`, `FALLBACK`, and `UNAVAILABLE`. | DN | `app/schemas/enums.py`; `app/schemas/responses.py`; provenance tests |
| RW-0006 | RW-000 Task 6 | Pin runtime/library versions and provide environment verification. | DN | `requirements.txt`; `verify_environment.py`; successful environment verification output |
| RW-0007 | RW-000 Task 7 | Use task IDs for assignment, branches and tightly related task groups; merge shared contracts before dependent code. | DN | Stage 0 task tracker and repository workflow documentation; final review completed |

## Current Evidence

### Environment Verification

```text
=== URAI Ransomware Resilience Environment Verification ===
Python: 3.14.0
FastAPI: 0.141.1
Pydantic: 2.13.4
httpx: 0.28.1
pytest: 9.1.1
Environment verification: PASS
```

### Test Verification

```text
............ [100%]
21 passed in 0.71s
```

## Stage 0 Supporting Artifacts
`docs/ransomware/repository_map.md`
`docs/ransomware/safety_policy.md`
`docs/ransomware/module_boundaries.md`
`requirements.txt`
`verify_environment.py`
`app/schemas/enums.py`
`app/schemas/responses.py`
`app/services/ransomware_mock.py`
`tests/test_api.py`
`tests/test_schemas.py`

## Review Notes

No real ransomware, encryption payload, detonation or operational action is implemented.
Dataset generation and model development remain outside the Stage 0 closure boundary.
The request/response API contract must be frozen before proceeding to dependent stages.
Stage 0 contract freeze and final passing test verification are complete.