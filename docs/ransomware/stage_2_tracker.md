# URAI Ransomware Resilience — Stage 2 Task Tracker

**Stage:** Stage 2 — Asset, Dependency Graph and Protected-Node Integrity
**Overall status:** IP — In Progress
**Status convention:** NS = Not Started, IP = In Progress, BL = Blocked, RV = Review, DN = Done

## Task status

| Local ID | Requirement | Status | Repository evidence |
|---|---|---|---|
| S2-01 | Verify Energy asset records, sector/site identifiers, and zones. | RV | `energy/assets.json`; `shared/zone_contract.py` |
| S2-02 | Verify Petrochemical asset records, sector/site identifiers, and zones. | RV | `petrochemical/assets.json`; `shared/zone_contract.py` |
| S2-03 | Verify Energy graph edges and canonical asset references. | RV | `energy/graph_edges.json`; `shared/graph_contract.py` |
| S2-04 | Verify Petrochemical graph edges and canonical asset references. | RV | `petrochemical/graph_edges.json`; `shared/graph_contract.py` |
| S2-05 | Prevent cross-sector and orphan graph references. | DN | `tests/ransomware/test_stage2_integrity.py` |
| S2-06 | Verify protected-node types, read-only access, and explicit boundaries. | RV | Both sectors' `protected_nodes.json`; `shared/protected_node_contract.py` |
| S2-07 | Prevent direct enterprise-IT edges to the protection/safety zone. | DN | `tests/ransomware/test_stage2_integrity.py` |
| S2-08 | Run Stage 2 integrity tests. | DN | Three recorded runs; 5 passed each time |

## Configuration inventory

| Configuration | Energy | Petrochemical | Total |
|---|---:|---:|---:|
| Assets | 10 | 11 | 21 |
| Graph edges | 9 | 11 | 20 |
| Protected nodes | 8 | 8 | 16 |
| **Total records** | **27** | **30** | **57** |

## Verified contracts

- Six canonical graph-edge types.
- Six canonical network zones.
- Eight canonical protected-node types.
- Protected-node access mode is restricted to `read_only`.
- Integrity tests check sector/site prefixes, zones, graph endpoints, edge types, sector separation, protected boundaries, and the enterprise-IT-to-protection/safety restriction.

## Verification record

Test file: `apps/ml-services/tests/ransomware/test_stage2_integrity.py`

Observed during this review: the test suite was run three times, with 5 tests passing on each run. Separate run logs are not persisted in this tracker.

These results verify the current integrity-test suite, not the completion of every Stage 2 requirement.

## Completion and safety notes

Stage 2 remains **In Progress** until the full Stage 2 task sheet and blueprint requirements have been reviewed. Rows marked RV require confirmation against those authoritative requirements.

This tracker does not claim production deployment, live OT validation, or a physical-safety determination. Human approval and non-execution boundaries remain unchanged.

Do not rerun, modify, or tune against the frozen holdout at `evaluation/final_holdout/archive_stale_20261005/`.

Dataset generation remains Stage 4, after Stages 2 and 3 pass their required reviews.
