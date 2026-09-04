# URAI Ransomware Resilience — Stage 1 Task Tracker

**Stage:** Stage 1 — Scope, Use Cases, Safety Boundaries and Acceptance Criteria
**Overall status:** RV — starter package ready for contributor/domain review
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Task status

| Tracker ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| RW-0101 | Define five energy ransomware-resilience use cases. | RV | `apps/ml-services/config/ransomware/energy/use_cases.json` |
| RW-0102 | Define five petrochemical ransomware-resilience use cases. | RV | `apps/ml-services/config/ransomware/petrochemical/use_cases.json` |
| RW-0103 | Freeze permitted industries and sector-specific site types. | RV | `industry_site_types.json`; contract tests |
| RW-0104 | Separate cyber incident stage from operational dependency consequence. | RV | `decision_operational_contract.json`; response schema; negative tests |
| RW-0105 | Provide safe explanatory recommendation templates and warnings. | RV | `recommendation_templates.json`; contract tests |
| RW-0106 | Freeze the five controlled asset states. | RV | `asset_states.json`; enum/schema tests |
| RW-0107 | Define measurable, sector-separated acceptance gates. | RV | `acceptance_gates.json`; threshold tests |

## Review required before Done

Yuvanka should review each use case against the detailed task sheet and FINAL v3 blueprint, confirm that the sector language and evidence are realistic, and record any proposed wording changes. A domain reviewer should confirm the safety statements and acceptance thresholds. After those approvals, commit the reviewed files with an `RW-01xx` traceable commit message and run the environment verifier and full test suite from a clean checkout.

Stage 2 must not begin until this tracker is changed from RV to DN with the reviewed commit hash and verification evidence. Dataset generation remains Stage 4, after Stages 2 and 3 also pass.

## Starter-package verification

```text
Python: 3.12.13
requirements.lock SHA-256: PASS
Environment verification: PASS
48 passed, 1 documented upstream deprecation warning
```

The count above must be reconfirmed after Yuvanka applies and reviews the package; it does not by itself change Stage 1 from RV to DN.
