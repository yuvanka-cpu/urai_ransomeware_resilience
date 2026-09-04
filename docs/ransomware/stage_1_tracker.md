# URAI Ransomware Resilience — Stage 1 Task Tracker

**Stage:** Stage 1 — Scope, Use Cases, Safety Boundaries and Acceptance Criteria
**Overall status:** Completed
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Task status

| Tracker ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| RW-0101 | Define five energy ransomware-resilience use cases. | DN | `apps/ml-services/config/ransomware/energy/use_cases.json` |
| RW-0102 | Define five petrochemical ransomware-resilience use cases. | DN | `apps/ml-services/config/ransomware/petrochemical/use_cases.json` |
| RW-0103 | Freeze permitted industries and sector-specific site types. | DN | `industry_site_types.json`; contract tests |
| RW-0104 | Separate cyber incident stage from operational dependency consequence. | DN | `decision_operational_contract.json`; response schema; negative tests |
| RW-0105 | Provide safe explanatory recommendation templates and warnings. | DN | `recommendation_templates.json`; contract tests |
| RW-0106 | Freeze the five controlled asset states. | DN | `asset_states.json`; enum/schema tests |
| RW-0107 | Define measurable, sector-separated acceptance gates. | DN | `acceptance_gates.json`; threshold tests |

## Completion

Stage 1 review was completed against the detailed task sheet and FINAL v3 blueprint. No domain or wording corrections were required. The human-approval and non-execution safety boundaries remain unchanged.

Final reviewed commit: `2abe435fc85bb9c1516eb9e1125cda04ad9aba58`

Clean-clone verification:
- requirements.lock SHA-256: PASS
- Environment verification: PASS
- Tests: 48 passed, 1 documented upstream deprecation warning

Stage 1 is complete. Stage 2 may begin. Dataset generation remains Stage 4, after Stages 2 and 3 also pass.

## Starter-package verification

```text
Python: 3.12.10
requirements.lock SHA-256: PASS
Environment verification: PASS
48 passed, 1 documented upstream deprecation warning
```

The above verification was reconfirmed after review and clean-clone verification. Stage 1 is now marked DN.
