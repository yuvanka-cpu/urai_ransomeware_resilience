# URAI Ransomware Resilience — Stage 3 Task Tracker

**Stage:** Stage 3 — Canonical Event Contracts, Normalization, Quality Gates and Data Isolation
**Overall status:** In Progress
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Task status

| Tracker ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| RW-0301 | Define the canonical observable-event schema and contract. | RV | `shared/schemas/canonical_event.avsc`; `shared/schemas/canonical_event_contract.md`; schema and validator tests; 33 focused validation, quality-gate, asset-compatibility and graph-integrity tests passed. |
| RW-0302 | Validate canonical events and reject invalid or incompatible values. | RV | `shared/validation/canonical_event_validator.py`; `tests/ransomware/test_canonical_event_validator.py`; quality-gate and asset-validation tests. |
| RW-0303 | Convert explicitly mapped source records into validated canonical events. | DN | `shared/canonical_event_converter.py`; `tests/ransomware/test_canonical_event_converter.py` |
| RW-0304 | Route invalid canonicalization and normalization data through the dead-letter contract. | RV | `shared/validation/canonical_dlq_router.py`; `shared/dlq_contract.py`; DLQ contract and routing tests |
| RW-0305 | Apply normalization, timestamp, identifier, numeric-value and asset-resolution checks. | RV | `shared/normalization.py`; `shared/validation/asset_registry.py`; `shared/validation/quality_gates.py`; focused tests |
| RW-0306 | Enforce event-time ordering, partition isolation and replay consistency. | RV | `shared/validation/event_time_ordering.py`; `shared/topics/partition_order_contract.md`; ordering tests |
| RW-0307 | Prevent truth-label and future-information leakage into deployed features. | RV | `shared/validation/feature_leakage_guard.py`; leakage-guard and split-isolation tests |
| RW-0308 | Define schema-evolution and registry compatibility policies. | RV | `shared/schemas/schema_evolution_contract.md`; `schema_evolution_policy.md`; `schema_registry_policy.md`; policy tests |
| RW-0309 | Enforce canonical metric units with a machine-readable registry and validate Cycle 3 measurement units. | RV | `shared/validation/canonical_feature_units.py` (seven approved derived-feature units); `shared/validation/canonical_metric_units.json` and `.py` (machine-readable canonical event metric registry and validation); `shared/validation/canonical_event_validator.py`; `shared/validation/quality_gates.py`; Cycle 3 evidence vocabulary, background measurements and validated-event adapter. Canonical event metrics are checked against the registry and unregistered names are rejected. The registry currently contains zero approved event metrics because no authoritative production metric definitions and units have been established; synthetic `risk_score` is not assigned an invented unit. The quality gate reports this explicitly as `EMPTY_NO_APPROVED_METRICS`. Cycle 3 vocabulary and adapter enforce measurement units; evidence-feature mapping validates source units, feature units and transformations for five compatible mappings, while seven unresolved mappings cannot declare unit or transformation metadata. Mapping contract and gate tests: 95 passed. Latest focused RW-0309 integration tests: 42 passed. Latest Cycle 3 tests: 654 passed, 567 deselected; one dependency deprecation warning. |
| RW-0310 | Verify the focused Stage 3 contract and integration test suites. | RV | Historical full-suite result: 1,202 passed before later changes. Latest broad run: 1,145 passed, 9 failed; eight failures blocked by missing PyTorch and one RW-0906 bundle checksum mismatch. Latest focused Stage 3 contract and integration suite: 538 passed. Latest focused Cycle 3 tests: 654 passed, 567 deselected; one dependency deprecation warning. |

## Verification record

Historical verification: the complete `apps/ml-services/tests/ransomware` suite passed 1,202 tests before the latest changes. The latest focused Stage 3 contract and integration suite passed 538 tests. The latest Cycle 3 test selection passed 654 tests, with 567 deselected and one Starlette/httpx deprecation warning. A later broad run reported 1,145 passed and 9 failed. Eight failures require the missing PyTorch dependency; one is an RW-0906 promoted-bundle checksum mismatch. The broad suite is therefore not currently green.

## Outstanding completion gate

The derived-feature registry defines and validates seven approved units. The shared window-feature extractor enforces that all seven registered features are present in its output. Online and offline processing use this extractor, and focused feature-parity tests have passed.

A separate machine-readable canonical event metric registry now exists at `shared/validation/canonical_metric_units.json`. The canonical event validator rejects unregistered metric names and unsupported schema versions. The quality gate validates both the derived-feature registry and the canonical event metric registry, and reports the number of registered event metrics.

The canonical event metric registry is currently empty. No authoritative production metric definitions and units have been established, so synthetic `risk_score` is deliberately not assigned an invented unit. Consequently, the enforcement mechanism is implemented, but approving and registering any actual production event metrics remains an explicit evidence-dependent step. Do not describe the empty registry as complete metric coverage.

The Cycle 3 validated-event adapter checks each generated background measurement's unit against its event-type vocabulary definition. The evidence-feature mapping contract validates source units against the shared vocabulary and enforces the expected output feature unit and transformation for all five compatible mappings. Seven unresolved mappings are rejected if they declare unit or transformation metadata. Latest focused RW-0309 tests: 42 passed. Latest Cycle 3 tests: 654 passed, 567 deselected; one dependency deprecation warning.

RW-0309 should remain under review until the canonical event metric inventory is confirmed and any approved production metrics have authoritative units registered, or the project owner explicitly confirms that no canonical event metrics are in scope for schema v1.0.

## Safety and evaluation boundaries

- Preserve the existing human-approval and non-execution safety boundaries.
- Do not introduce operational actions against protected OT or safety systems.
- Do not rerun, modify or tune against `evaluation/final_holdout/archive_stale_20261005/`.
- Any future holdout evaluation requires a separately controlled evaluation cycle.

## Completion

Stage 3 remains In Progress. Reassess the review rows and close the canonical-unit gate before marking the stage complete.
