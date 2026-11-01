# URAI Ransomware Resilience — Stage 3 Task Tracker

**Stage:** Stage 3 — Canonical Event Contracts, Normalization, Quality Gates and Data Isolation
**Overall status:** In Progress
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Task status

| Tracker ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| RW-0301 | Define the canonical observable-event schema and contract. | RV | `shared/schemas/canonical_event.avsc`; `shared/schemas/canonical_event_contract.md`; schema and validator tests |
| RW-0302 | Validate canonical events and reject invalid or incompatible values. | RV | `shared/validation/canonical_event_validator.py`; `tests/ransomware/test_canonical_event_validator.py`; negative fixtures |
| RW-0303 | Convert explicitly mapped source records into validated canonical events. | DN | `shared/canonical_event_converter.py`; `tests/ransomware/test_canonical_event_converter.py` |
| RW-0304 | Route invalid canonicalization and normalization data through the dead-letter contract. | RV | `shared/validation/canonical_dlq_router.py`; `shared/dlq_contract.py`; DLQ contract and routing tests |
| RW-0305 | Apply normalization, timestamp, identifier, numeric-value and asset-resolution checks. | RV | `shared/normalization.py`; `shared/validation/asset_registry.py`; `shared/validation/quality_gates.py`; focused tests |
| RW-0306 | Enforce event-time ordering, partition isolation and replay consistency. | RV | `shared/validation/event_time_ordering.py`; `shared/topics/partition_order_contract.md`; ordering tests |
| RW-0307 | Prevent truth-label and future-information leakage into deployed features. | RV | `shared/validation/feature_leakage_guard.py`; leakage-guard and split-isolation tests |
| RW-0308 | Define schema-evolution and registry compatibility policies. | RV | `shared/schemas/schema_evolution_contract.md`; `schema_evolution_policy.md`; `schema_registry_policy.md`; policy tests |
| RW-0309 | Enforce canonical metric units with a machine-readable registry. | RV | `shared/validation/canonical_feature_units.py`; `shared/validation/quality_gates.py`; `features/window_features.py`; canonical-unit, window-feature, feature-parity and quality-gate tests: 39 passed. Registry validates seven derived-feature unit declarations and the shared extractor rejects missing registered features. |
| RW-0310 | Verify the focused Stage 3 contract and integration test suites. | DN | After final RW-0309 changes, full `tests/ransomware` suite: 1,202 passed. |

## Verification record

After the RW-0309 implementation changes, the complete `apps/ml-services/tests/ransomware` suite passed: 1,202 tests. This is the latest regression result; rerun relevant tests after subsequent implementation changes.

## Outstanding completion gate

A machine-readable registry now defines and validates the seven approved derived-feature units. The `canonical_units` quality gate calls this validator and reports registry validation errors instead of passing unconditionally.

The quality gate validates registry definitions, while the shared window-feature extractor enforces that all seven registered features are present in its output. Online and offline processing both use this extractor; the focused feature-parity tests passed.

This does not validate unit metadata attached to each individual incoming event metric, nor independently prove every source-evidence mapping uses the declared physical unit. Keep this limitation explicit; do not claim broader event-level unit validation.

## Safety and evaluation boundaries

- Preserve the existing human-approval and non-execution safety boundaries.
- Do not introduce operational actions against protected OT or safety systems.
- Do not rerun, modify or tune against `evaluation/final_holdout/archive_stale_20261005/`.
- Any future holdout evaluation requires a separately controlled evaluation cycle.

## Completion

Stage 3 remains In Progress. Reassess the review rows and close the canonical-unit gate before marking the stage complete.
