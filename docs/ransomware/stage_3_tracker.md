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
| RW-0309 | Enforce canonical metric units with a machine-readable registry and validate Cycle 3 measurement units. | RV | `shared/validation/canonical_feature_units.py`; `shared/validation/quality_gates.py`; `features/window_features.py`; Cycle 3 evidence vocabulary, background measurements and validated-event adapter. Seven derived-feature units are registered; Cycle 3 measurements carry vocabulary-defined units and the adapter rejects missing or mismatched units. The evidence-feature mapping contract now validates source units, exact feature units and transformations for all five compatible mappings; seven unresolved mappings cannot declare unit or transformation metadata. Mapping contract and gate tests: 95 passed; earlier focused Cycle 3 tests: 159 passed. Converter-to-Parquet round-trip test verifies exact canonical event value preservation and post-read validation; converter, Parquet reader and parity tests: 13 passed. This does not establish general metric-unit validation or full online/offline unit parity: canonical event metrics remain unitless in schema v1.0, and no authoritative registry exists for all metric keys. |
| RW-0310 | Verify the focused Stage 3 contract and integration test suites. | RV | Historical full-suite result: 1,202 passed before later changes. Latest broad run: 1,145 passed, 9 failed; eight failures blocked by missing PyTorch and one RW-0906 bundle checksum mismatch. Latest focused Cycle 3 tests: 159 passed. |

## Verification record

Historical verification: the complete `apps/ml-services/tests/ransomware` suite passed 1,202 tests before the latest changes. After the Cycle 3 unit-validation changes, the three focused Cycle 3 test modules passed 159 tests. A later broad run reported 1,145 passed and 9 failed. Eight failures require the missing PyTorch dependency; one is an RW-0906 promoted-bundle checksum mismatch. The broad suite is therefore not currently green.

## Outstanding completion gate

A machine-readable registry now defines and validates the seven approved derived-feature units. The `canonical_units` quality gate calls this validator and reports registry validation errors instead of passing unconditionally.

The quality gate validates registry definitions, while the shared window-feature extractor enforces that all seven registered features are present in its output. Online and offline processing both use this extractor; the focused feature-parity tests passed.

The Cycle 3 validated-event adapter checks each generated background measurement's unit against its event-type vocabulary definition. The evidence-feature mapping contract now independently validates source units against the shared vocabulary and enforces the expected output feature unit and transformation for all five compatible mappings. Seven unresolved mappings are rejected if they declare unit or transformation metadata. The mapping contract and mapping-gate tests pass 95 tests. This remains scoped to the known Cycle 3 mappings: it does not add general unit metadata validation to the broader canonical event converter/validator. Keep that limitation explicit.

## Safety and evaluation boundaries

- Preserve the existing human-approval and non-execution safety boundaries.
- Do not introduce operational actions against protected OT or safety systems.
- Do not rerun, modify or tune against `evaluation/final_holdout/archive_stale_20261005/`.
- Any future holdout evaluation requires a separately controlled evaluation cycle.

## Completion

Stage 3 remains In Progress. Reassess the review rows and close the canonical-unit gate before marking the stage complete.
