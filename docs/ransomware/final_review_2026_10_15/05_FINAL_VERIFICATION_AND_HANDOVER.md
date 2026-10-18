# URAI — Final Verification and Handover

## 1. Project Status

URAI is a synthetic, defensive ransomware-resilience research prototype
for energy and petrochemical environments.

The implementation has demonstrated working backend API inference,
frontend buildability, automated test coverage, and human-approval
safety controls.

The system has NOT passed its final detection-quality acceptance gate
and must NOT be represented as production-ready.

## 2. Verified Automated Tests

The following verification results were recorded during the final review:

| Verification | Result |
|---|---|
| Ransomware Python test suite | 1,139 passed |
| Backend Python tests | 6 passed |
| Frontend Vitest tests | 102 passed |
| Total automated tests | 1,247 passed |
| Frontend production build | Passed |
| Backend health endpoint | HTTP 200 |

These results were obtained through separate test executions.
They do not establish operational deployment readiness.

## 3. Public Backend Inference Verification

A schema-valid synthetic request was submitted to:

POST /api/v1/ransomware/infer

Observed result:

- HTTP status: 200
- Runtime state: live_model
- Artifact status: loaded
- Data provenance: LIVE_MODEL
- Model bundle: rw0906_v2
- Industry: energy
- Site type: substation
- Scenario ID: rw-attack-070891bdbaec
- Decision: normal
- Human approval required: true
- Real action executed: false
- Synthetic-only runtime contract: true
- Physical safety determination: not_determined
- Recorded request latency: 501.414 ms

LIVE_MODEL identifies the inference runtime and does not mean
that live industrial telemetry was used.

The test demonstrated public backend inference integration.
It did not establish successful attack detection.

## 4. Detection-Quality Acceptance

The frozen final holdout evaluated on 5 October 2026 failed
its acceptance requirements.

Recorded limitations included:

- Attack recall: 0
- Attack precision: 0
- Frontend P95 latency: approximately 1.66 seconds
- Final decision: HOLD_FOR_NEW_EVALUATION_CYCLE

The frozen holdout must not be modified, replaced, or rerun
to manufacture a passing result.

The synthetic attack-labelled scenario used during the public
API verification also received a normal decision.

No production detection-performance claim is justified.

## 5. Model and Runtime Limitations

Known limitations include:

- Temporal challenger unavailable and excluded from calibration.
- Canonical inference response contract incomplete.
- Incident stage, severity, resilience score, and full asset/recovery
  context are not supplied by the current internal inference response.
- Physical safety is not determined by the model.
- Synthetic evidence does not establish real-world industrial accuracy.
- No autonomous containment or destructive action is permitted.

## 6. Cycle 3 Research Status

Cycle 3 contains exploratory scenario, measurement, evidence-quality,
feature-availability, and timeline-adapter implementations.

The exploratory dataset contains 420 synthetic scenarios.

The evidence review identified incomplete measurement coverage
across the intended ransomware use cases.

Additional limitations include:

- Several required evidence domains remain unsupported.
- Some background measurements do not distinguish scenario variants.
- Timeline adapter compatibility remains unresolved.
- Scenario effects have not been physically validated.
- Cycle 3 has not passed a defensible model-training readiness gate.

Cycle 3 must be treated as incomplete research infrastructure,
not as a validated replacement model or production dataset.

No new holdout was created as part of this handover.

## 7. Safety Boundaries

URAI is restricted to synthetic defensive analysis.

Required safety principles:

- human_approval_required = true
- real_action_executed = false
- No ransomware execution or encryption payloads.
- No destructive file operations.
- No autonomous containment or industrial control actions.
- Missing or incompatible evidence must not be silently
  represented as a normal operational state.

Recommendations require qualified human review.

## 8. Git and Artifact Preservation

The final review identified modified historical ML artifacts
and frozen evaluation files in the working tree.

These files require separate provenance and integrity review.

Do not indiscriminately stage the entire repository.

In particular:

- Preserve frozen final-holdout files and their archives.
- Do not reset or overwrite historical evaluation evidence.
- Exclude temporary backup files from the handover commit.
- Do not promote incomplete Cycle 3 work as validated ML output.
- Stage only explicitly reviewed files.

## 9. Final Handover Assessment

Verified:

- Automated test suites pass.
- Frontend production build succeeds.
- Public backend inference returns a structured model response.
- Human-approval and no-real-action flags are present and correct.
- Synthetic-only and physical-safety limitations are disclosed.

Not verified or not accepted:

- Final attack-detection performance.
- Production latency acceptance.
- Complete canonical inference contract.
- Cycle 3 training readiness.
- Real industrial deployment safety.
- Full browser-based end-to-end deployment.

Final classification:

RESEARCH PROTOTYPE — INTEGRATION VERIFIED;
DETECTION ACCEPTANCE FAILED;
NOT PRODUCTION-READY.
