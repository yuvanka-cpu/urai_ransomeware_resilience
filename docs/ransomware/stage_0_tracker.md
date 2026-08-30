# URAI Ransomware Resilience — Stage 0 Task Tracker

**Stage:** Stage 0 — Repository Readiness, Boundaries and Execution Controls
**Overall status:** RV — ready for independent review
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Objective

Establish the working repository, safe operating boundary, reproducible environment and task-control method before scenario, dataset or model implementation.

## Task status

| Tracker ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| RW-0001 | Confirm backend, frontend and ML-service roots with existing/planned status. | DN | `docs/ransomware/repository_map.md` |
| RW-0002 | Create the application, configuration, synthetic-data, test, artifact and documentation skeleton without placeholder model decisions. | DN | Retained README skeletons; repository map |
| RW-0003 | Version the synthetic-only, non-executing safety policy. | DN | `docs/ransomware/safety_policy.md`; safety/API tests |
| RW-0004 | Freeze decision states and fixed approval/execution fields. | DN | `app/schemas/enums.py`; `app/schemas/responses.py`; exact-cause tests |
| RW-0005 | Freeze controlled provenance values. | DN | `app/schemas/enums.py`; provenance tests |
| RW-0006 | Pin runtime/libraries, record a lock checksum and verify the environment. | DN | `.python-version`; `requirements.lock`; checksum; verifier output below |
| RW-0007 | Use RW task IDs in branches/commits/reviews and provide repository traceability. | RV | Workflow requirement documented; repository URL and remote commit hash must be supplied by the repository owner |

## Independent environment evidence

```text
Python: 3.12.13
All 17 locked packages matched exact versions.
requirements.lock SHA-256: PASS
Environment verification: PASS
```

Command from `apps/backend`:

```powershell
..\..\.venv\Scripts\python.exe verify_environment.py
```

## Independent test evidence

```text
..................................... [100%]
37 passed, 1 documented upstream deprecation warning
```

Command from `apps/backend`:

```powershell
..\..\.venv\Scripts\python.exe -m pytest -q
```

The warning is documented in `docs/ransomware/known_warnings.md` and is not suppressed.

## Review boundary

- No malware, encryption payload, detonation, destructive action, active probing or operational action is implemented.
- Dataset generation and model development remain outside Stage 0.
- The safety/decision/provenance sub-contract is frozen; Stage 1–3 domain contracts remain governed future work.
- Stage 0 may be approved after an independent reviewer confirms the package and the repository owner supplies the repository URL and exact remote commit hash for RW-0007.

## Repository-owner evidence still required

```text
Repository URL: TO BE PROVIDED BY YUVANKA
Reviewed commit hash: TO BE PROVIDED BY YUVANKA
```
