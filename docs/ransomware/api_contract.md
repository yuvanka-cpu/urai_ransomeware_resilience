# URAI Ransomware Resilience — Stage 0 API Baseline

**Status:** REVIEW — core safety/decision/provenance sub-contract frozen
**Schema version:** `1.0`
**Scope:** Defensive synthetic PoC; recommendation/review only

## Contract status

Stage 0 freezes the decision states, provenance values and non-execution safety invariants. Sector use cases, asset states, canonical events, scenario metadata and synthetic-truth schemas are completed in Stages 1–3; those later fields must not be described as frozen prematurely.

## Request

Source: `apps/backend/app/schemas/requests.py`

| Field | Contract |
|---|---|
| `schema_version` | exactly `1.0` |
| `use_case` | exactly `ransomware_resilience` |
| `industry` | `energy` or `petrochemical` |
| `site_id` | non-blank string |
| `site_type` | `control_centre`, `substation`, `refinery` or `petrochemical_complex` |
| `scenario_id` | non-blank string |
| `observable_input` | observable synthetic dictionary; reserved truth keys rejected recursively |

Unexpected top-level fields are rejected. Reserved `ground_truth`, `ground_truth_label`, `synthetic_truth` and `truth_label` keys are rejected at any depth inside `observable_input`. The final typed observable event contract is a Stage 3 deliverable.

## Response

Source: `apps/backend/app/schemas/responses.py`

The response contains sector/site/scenario context, decision and incident stage, bounded confidence and resilience score, separate affected and suspected asset collections, dependency/evidence/timeline collections, typed backup readiness, explanations, recommendations, typed artifact provenance, data provenance, warnings, request/trace identifiers and a controlled runtime state.

### Fixed safety fields

```text
human_approval_required = true
real_action_executed = false
```

No API path may execute malware, encryption, destructive behavior, containment, recovery, restore, startup or operational-control actions.

### Decision values

- `normal`
- `investigate`
- `high_risk`
- `unavailable`

### Provenance values

- `LIVE_MODEL`
- `SYNTHETIC_GROUND_TRUTH`
- `STATIC_SCENARIO_METADATA`
- `DERIVED_BY_BACKEND`
- `FALLBACK`
- `UNAVAILABLE`

### Runtime states

- `mocked`
- `live_model`
- `degraded`
- `fallback`
- `unavailable`

Fallback and unavailable states remain visibly distinct from live success. Required dependency or artifact failures must never silently produce a normal decision.

## Stage 0 fixtures

The `/mock/normal`, `/mock/investigate`, `/mock/high-risk`, `/mock/fallback` and `/mock/unavailable` routes exercise the response contract. They are explicitly synthetic contract fixtures and not placeholder model decisions.

## Change control

Changes to decision, provenance or safety invariants require explicit review, versioning and negative tests. Stage 1–3 additions must preserve backward safety constraints and update the schema version when compatibility requires it.
