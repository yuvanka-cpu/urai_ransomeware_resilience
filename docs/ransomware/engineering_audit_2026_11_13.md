# URAI Ransomware Resilience — Engineering Audit

**Audit date:** 2026-11-13
**Branch:** `rw-cycle-2-quality-improvement`
**Audited HEAD:** `f490b7a1a7ef90e6b84410ab32ab910c49147baa`
**Commit:** `fix(rw-0906): restore promoted bundle artifacts`

## 1. Overall assessment

URAI is a synthetic, defensive ransomware-resilience research prototype.

**Classification:** RESEARCH PROTOTYPE — INTEGRATION VERIFIED IN PART; DETECTION ACCEPTANCE FAILED; NOT PRODUCTION-READY.

This audit reviews implementation, available reports, trackers and selected tests. It does not certify production readiness, real-world detection accuracy, physical safety or live OT/ICS compatibility.

## 2. Stage-by-stage audit position

| Stage | Audit position | Findings |
|---|---|---|
| 0 | Historically verified | Tracker records environment and backend verification. Historical evidence is not a fresh run at this HEAD. |
| 1 | Historically verified | Tracker records use cases and acceptance requirements. Historical evidence is not a fresh run at this HEAD. |
| 2 | In progress | Asset, graph and protected-node configurations inspected. 18 relevant tests passed. Authoritative task sheet/blueprint review remains outstanding. |
| 3 | In progress | Schema, validation and unit enforcement have substantial implementation and test evidence. RW-0309 still needs an owner decision on the canonical metric inventory or confirmation that schema v1.0 has no approved canonical event metrics. |
| 4 | Incomplete | Cycle 3 has 420 exploratory synthetic scenarios, but measurement coverage and training-readiness evidence are incomplete. |
| 5 | Partially verified | Split isolation and related checks have evidence. A dedicated integrity/tampering test for the original split-assignment manifest was not found in the reviewed tests. |
| 6 | Partially verified | Feature extraction and parity checks have evidence. Cycle 2 training actively enriches all scenarios before feature extraction. Event-type-specific synthetic telemetry patterns may create artificial separability; dedicated enrichment behaviour tests were not found. |
| 7 | Detection acceptance failed | Training and evaluation artifacts exist, but reported detection metrics are weak. Cross-validation recall was 0 and 0.333; frozen validation recall was 0.50. |
| 8 | Decision verified; evidence limits remain | Challenger rejection decision is documented. No temporal or learned graph challenger was promoted; deterministic weighted graph baseline retained. |
| 9 | Component verification strong | Availability contract, promoted bundle checksums and rejected challenger registry have focused test evidence. |
| 10 | Component verification strong | 77 selected tests passed. Artifact loading, feature contract, inference assembly and unavailable behaviour have negative-test coverage. Full end-to-end gate remains unverified. |
| 11 | Integration components verified | 33 selected backend tests passed, covering routes, gateway, orchestration, safety, audit and degradation. |
| 12 | Blocked by environment | 14 backend/ML timeline tests passed. Frontend tests and build could not be run because Node.js/npm and alternative runtimes were unavailable. |
| 13 | Monitoring components verified; capabilities limited | 55 selected tests passed. Model drift and incident timing correctly report unavailable where supporting evidence is absent. |
| 14 | Historical acceptance failed; sealed | Historical final holdout failed detection acceptance. No rerun, modification or tuning is permitted. |
| 15 | Focused validation verified | 15 selected tests passed for response validation and malformed gateway responses. Handover documentation exists; current clean-checkout reproduction is not established. |

These are audit positions, not replacement tracker statuses or formal owner sign-offs.

## 3. Selected test evidence

The following are test results supplied during this audit. They are focused selections, not one complete repository-wide test run.

| Scope | Result |
|---|---:|
| Stage 2 identifier/protected-node/integrity tests | 18 passed |
| Stage 5 selected split/isolation/quality-gate tests | 55 passed |
| Stage 6 selected feature/parity/contract tests | 83 passed |
| Stage 8/9 selected challenger/promotion/availability tests | 24 passed |
| Stage 9 availability/bundle/rejected-registry tests | 13 passed |
| Stage 10 selected tests | 77 passed, 1 warning |
| Stage 11 selected backend tests | 33 passed, 1 warning |
| Stage 12 timeline backend/ML tests | 14 passed |
| Stage 13 monitoring tests | 55 passed |
| Stage 15 response validation/gateway tests | 15 passed |

Stage 0 and Stage 1 tracker results are historical. The Stage 3 tracker also contains historical focused and broad-suite results; the broad suite was not green in the latest recorded run. Do not interpret the table as a fresh full-suite result.

## 4. Material engineering findings

### 4.1 Detection quality

The October 2026 final review records that the frozen final holdout failed, with attack recall 0 and attack precision 0. The recorded decision was `HOLD_FOR_NEW_EVALUATION_CYCLE`.

The Stage 7 test-split scorecard also records weak performance, including low recall and high false-positive rate. A successful integration test or model artifact load does not establish detection acceptance.

### 4.2 Synthetic-data realism

`catboost_trainer.py` calls `build_rows(frozen, cycle2=True)`. This activates `enrich_cycle2_events()` before feature extraction.

The reviewed enrichment function assigns distinct synthetic values based on event type, including stage-transition scores, encryption-impact file activity, entropy proxies and recovery-impairment signals. Benign lookalikes receive their own patterns.

This does not prove direct label leakage, but it raises a material synthetic-realism and evaluation-validity concern. No dedicated test invoking the enrichment function was found in the reviewed test search. Independent-data generalisation is not demonstrated.

### 4.3 Split-manifest integrity

Training and evaluation provenance record SHA-256 hashes of the source split manifest. The promoted model bundle also has checksummed files and loader tampering tests.

However, a dedicated negative test proving that a tampered original split-assignment manifest is rejected before its assignments are used was not found in the reviewed tests. Provenance hashing should not be confused with input-manifest integrity enforcement.

### 4.4 Canonical metric units

The canonical metric registry is version 1.0, compatible with schema 1.0, and intentionally has an empty `metrics` object until production metric semantics and units are formally defined.

Do not invent metric units or register synthetic `risk_score` as an approved canonical event metric. RW-0309 remains under review pending an owner decision.

### 4.5 Frontend verification

Frontend tests and production build were not run because Node.js, npm, Bun and Deno were unavailable in the audited environment. This is an environment blocker, not evidence that the frontend tests fail.

## 5. Safety and holdout restrictions

- Human approval remains required.
- Real operational actions remain disabled.
- No autonomous containment or live industrial control action is established.
- Physical safety determination remains `not_determined`.
- Synthetic evidence does not establish real-world detection accuracy.
- Missing, corrupt, incompatible, stale or slow evidence must remain unavailable; silent substitution is forbidden.
- The frozen directory `evaluation/final_holdout/archive_stale_20261005/` must not be inspected, rerun, modified or used for tuning.

## 6. Working-tree state at audit close

The working tree contained these pre-existing local changes:

- Modified: `apps/ml-services/config/ransomware/shared/identifier_contract.py`
- Modified: `apps/ml-services/tests/ransomware/test_identifier_contract.py`
- Untracked: `docs/ransomware/claude.txt`

The identifier-contract changes were covered by the 18 passing Stage 2 tests. The untracked `claude.txt` file contains only the word `claude` and is not engineering evidence.

Do not discard the identifier-contract changes. Do not stage the placeholder file without an explicit decision.

## 7. Recommended follow-up order

1. Obtain owner decisions for the Stage 2 authoritative requirements and Stage 3 canonical metric inventory.
2. Resolve Stage 5 split-manifest integrity requirements.
3. Document and address Stage 6 synthetic enrichment realism and test coverage.
4. Complete Stage 4 Cycle 3 measurement/readiness evidence before claiming training readiness.
5. Run frontend tests and build in an environment with a supported Node.js toolchain.
6. Keep detection acceptance failed until a separately authorised evaluation cycle provides defensible evidence. The frozen historical holdout remains sealed.

## 8. Audit limitations

This report records the evidence reviewed and test outputs supplied during the audit. It is not a clean-clone reproduction, complete source-code certification, production security assessment, independent model validation or operational safety approval.

No code changes, commits or pushes were made as part of the read-only audit. This report itself is a new documentation artifact and should be reviewed before staging or committing.
