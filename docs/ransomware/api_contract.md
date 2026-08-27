# URAI Ransomware Resilience — Frozen API Contract

**Status:** FROZEN — Stage 0  
**Scope:** Energy & Petrochemical Ransomware Resilience Synthetic PoC  
**Contract type:** Request/response schema contract  
**Safety classification:** Defensive synthetic PoC; recommendation/review only

## 1. Purpose

This document records the request and response API contract frozen at the
completion of Stage 0.

The contract is the shared controlled interface between the backend,
future ML-service orchestration, frontend, tests, and later dashboard
implementation.

Changes to this contract after Stage 0 require explicit review and must not
silently break dependent components.

---

## 2. Request Contract

The canonical ransomware request is defined by
`app/schemas/requests.py`.

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | string | Identifies the request contract version |
| `use_case` | string | Identifies the ransomware resilience use case |
| `industry` | string | Energy or petrochemical context |
| `site_id` | string | Synthetic site identifier |
| `site_type` | string | Synthetic site classification |
| `scenario_id` | string | Synthetic scenario identifier |
| `observable_input` | object/dict | Observable synthetic input data |

Synthetic ground truth must not be supplied through `observable_input`.

---

## 3. Response Contract

The canonical ransomware response is defined by
`app/schemas/responses.py`.

### Context

- `use_case`
- `industry`
- `site_id`
- `site_type`
- `scenario_id`

### Decision and Assessment

- `decision`
- `incident_stage`
- `confidence`
- `severity`
- `resilience_score`

`confidence` represents calibrated model probability when model inference is
available.

### Asset and Dependency Context

- `affected_assets`
- `suspected_assets`
- `critical_services_at_risk`
- `affected_zones`
- `protected_boundaries`
- `operational_dependency_impact`

`affected_assets` and `suspected_assets` remain separate so exposure is not
represented as confirmed compromise.

### Evidence and Progression

- `propagation_path`
- `evidence_layers`
- `triggered_rules`
- `timeline`

### Recovery and Recommendations

- `backup_readiness`
- `explanations`
- `recommended_actions`

Recommendations are non-executing review outputs.

### Safety and Approval Controls

- `human_approval_required` — fixed to `true`
- `real_action_executed` — fixed to `false`

The PoC cannot execute containment, recovery, operational control, malware,
encryption, destructive behavior, or other operational actions.

### Provenance and Runtime Context

- `artifact_provenance`
- `data_provenance`
- `warnings`
- `request_id`
- `trace_id`
- `runtime_state`

`data_provenance` uses the controlled values defined by `DataProvenance`:

- `LIVE_MODEL`
- `SYNTHETIC_GROUND_TRUTH`
- `STATIC_SCENARIO_METADATA`
- `DERIVED_BY_BACKEND`
- `FALLBACK`
- `UNAVAILABLE`

---

## 4. Controlled Decision States

The `decision` field uses the `Decision` enum:

- `normal`
- `investigate`
- `high_risk`
- `unavailable`

`unavailable` is used when the runtime, artifact, schema, or safety
contract prevents a valid decision.

---

## 5. Controlled Incident Stages

The `incident_stage` field uses the `IncidentStage` enum:

- `none`
- `precursor`
- `credential_misuse`
- `lateral_movement`
- `staging`
- `encryption_impact`
- `recovery`

---

## 6. Controlled Severity

The `severity` field uses the `Severity` enum:

- `low`
- `medium`
- `high`
- `critical`

---

## 7. Runtime and Fallback Rules

The API must preserve visible degraded, fallback, and unavailable behavior.

Fallback content must be explicitly identified as `FALLBACK`.

`UNAVAILABLE` must remain distinct from successful inference.

Missing, stale, corrupt, incompatible, or unavailable dependencies must not
silently produce a normal decision.

Warnings are mandatory and must not be suppressed by the frontend.

---

## 8. Contract Safety Rules

1. Synthetic truth remains separate from observable inference input.
2. Synthetic ground truth must never be accepted as an inference feature.
3. Recommendations remain non-executing.
4. `human_approval_required` remains `true`.
5. `real_action_executed` remains `false`.
6. The frontend must not call the ML service directly.
7. The backend remains the orchestration boundary.
8. No API path may execute malware, encryption payloads, destructive
   behavior, containment, recovery, or operational control actions.

---

## 9. Source-of-Truth Implementation Files

The frozen contract is implemented by:

- `apps/backend/app/schemas/requests.py`
- `apps/backend/app/schemas/responses.py`
- `apps/backend/app/schemas/enums.py`

Validation evidence is provided by:

- `apps/backend/tests/test_schemas.py`
- `apps/backend/tests/test_api.py`

---

## 10. Freeze Record

**Stage 0 contract status:** FROZEN

**Request schema:** Confirmed

**Response schema:** Confirmed

**Decision states:** Confirmed

**Incident stages:** Confirmed

**Severity states:** Confirmed

**Controlled provenance values:** Confirmed

**Mandatory approval field:** `true`

**Real action field:** `false`

**Contract test status:** PASS

**Current test result:** 12 passed

Any future contract change must be explicitly reviewed, versioned, tested,
and documented before dependent implementation proceeds.