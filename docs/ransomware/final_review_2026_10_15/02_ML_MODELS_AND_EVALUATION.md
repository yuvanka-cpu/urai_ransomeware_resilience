# URAI — ML Models and Evaluation
Review: 15 October 2026
Status: Synthetic defensive proof of concept; not production-ready.

## Objective
Identify ransomware-related patterns in synthetic observable cybersecurity evidence.

## Pipeline
54 observable features -> Rules / Anomaly / CatBoost / Graph -> Missingness indicators -> Regularized logistic stacking -> Calibration -> Decision thresholds.

Temporal evidence remains unavailable.

Synthetic scenario labels must not enter inference inputs.

## Models
Rules provide deterministic evidence.
Anomaly detection measures deviations from development patterns.
CatBoost supplies supervised classification evidence.
Graph propagation supplies relationship-based evidence.
Logistic stacking combines available evidence and missingness indicators.

## Calibration
Recorded Cycle 2 development results:

| Metric | Before | After |
|---|---:|---:|
| Brier | 0.2653 | 0.2340 |
| Log loss | 0.7357 | 0.6606 |
| ECE | 0.1847 | 0.1315 |

## Thresholds
Investigate: 0.410065
High risk: 0.439306

## Development Results
High-risk recall: 0.125
Investigate-or-higher recall: 0.750
Benign false-positive rate: 0.4643

## Frozen Holdout Evaluation — 5 October 2026
The frozen RW-140 evaluation executed all 20 synthetic scenarios exactly once:
16 non-attack scenarios and 4 attack scenarios.

| Quality gate | Observed | Required | Status |
|---|---:|---:|---|
| Attack recall | 0.000 | >= 0.90 | FAIL |
| Precision | 0.000 | >= 0.85 | FAIL |
| Non-attack false-positive rate | 0.000 | <= 0.10 | PASS |
| Frontend-facing P95 latency | 1655.66 ms | < 1000 ms | FAIL |
| Scenarios scored | 20/20 | 20/20 | PASS |
| Human approval required | True | True | PASS |
| Real action executed | False | False | PASS |
| Progression metrics | Unavailable | Available | FAIL |
| Localization metrics | Unavailable | Available | FAIL |

Confusion matrix: TP=0, TN=16, FP=0, FN=4.
All four attack scenarios were missed at the evaluated decision threshold.

Final gate decision: HOLD_FOR_NEW_EVALUATION_CYCLE.

The frozen evaluation is not evidence of reliable ransomware detection.
Its frontend-facing latency is distinct from the newer Cycle 2 internal ML
benchmark; those measurements must not be presented as equivalent.

The October 4 historical holdout was superseded by the October 5 frozen
evaluation. Historical and Cycle 2 development results must remain separate.
No features, models, calibration, or thresholds may be retuned using the
frozen holdout results. Remediation requires a newly declared evaluation
cycle and a new untouched holdout.

## Data Drift
Offline PSI comparison: 54 training rows and 54 validation rows.
PSI threshold: 0.2.

Flagged:
- observable_value_max: 0.5768
- remote_admin_peer_count: 0.2182

Operational model drift remains unavailable.

## Incident Metrics
Offline MTTD, mean response time and mean recovery time calculator.
No verified operational incident timestamp dataset is connected.

## Latency
Internal Cycle 2 benchmark:
P50: 102.001 ms
P95: 114.472 ms
Maximum: 146.901 ms

These are not production latency guarantees.

## Responsible AI
Human approval required.
No real action executed.
Missing evidence remains unavailable.
Cybersecurity probabilities do not establish physical-safety consequences.

## Conclusion
Integrated synthetic ML decision-support pipeline.
Detection-quality gates failed; production deployment is not justified.
