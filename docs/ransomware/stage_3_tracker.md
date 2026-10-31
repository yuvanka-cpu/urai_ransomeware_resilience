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
| RW-0309 | Enforce canonical metric units with a machine-readable registry. | BL | `shared/validation/quality_gates.py` currently reports `canonical_units` as `CONTRACT_ONLY`; no authoritative machine-readable unit registry was found in the reviewed paths |
| RW-0310 | Verify the focused Stage 3 contract and integration test suites. | DN | Two separate focused batches: 150 tests passed in the first batch and 161 in the second; these are not a combined total. Rerun after final changes. |

## Verification record

The developer reported 150 passing tests in the first focused batch and 161 passing tests in the second focused batch. These are separate results, not a combined total.

These results establish passing focused test batches, not completion of every Stage 3 requirement. The tests must be rerun after any subsequent implementation changes.

## Outstanding completion gate

The canonical event contract requires online and offline processing to use the same canonical definitions and units. The current quality-gate implementation sets `canonical_units.passed` to `True` while marking its status `CONTRACT_ONLY`.

A passing result therefore does not currently establish that metric units are machine-validated. Do not claim Stage 3 complete until the authoritative metric-unit definitions are established and enforcement is implemented and tested.

Do not invent unit definitions. Resolve this against an authoritative project contract or approved source mapping.

## Safety and evaluation boundaries

- Preserve the existing human-approval and non-execution safety boundaries.
- Do not introduce operational actions against protected OT or safety systems.
- Do not rerun, modify or tune against `evaluation/final_holdout/archive_stale_20261005/`.
- Any future holdout evaluation requires a separately controlled evaluation cycle.

## Completion

Stage 3 remains In Progress. Reassess the review rows and close the canonical-unit gate before marking the stage complete.
