# URAI — Responsible AI, Governance and Known Limitations

**Review date:** 15 October 2026  
**Project:** Energy & Petrochemical Ransomware Resilience  
**Development context:** SPECTRA AI internship  
**Classification:** Defensive synthetic proof of concept  
**Deployment status:** Not production-ready

---

## 1. Responsible AI Objective

URAI is designed to support human cybersecurity investigation rather than replace human judgment.

Its intended use is defensive ransomware-resilience analysis in synthetic energy and petrochemical scenarios.

The system must provide transparent evidence, preserve uncertainty, and avoid unauthorized operational actions.

Responsible AI requirements are especially important because cybersecurity alerts may relate to environments containing industrial-control and safety-critical systems.

A model-generated cybersecurity score is not a determination of physical safety.

---

## 2. Core Responsible AI Principles

URAI's governance approach emphasizes:

1. Human oversight
2. Transparency and explainability
3. Evidence provenance
4. Reliability and robustness
5. Safety and non-execution
6. Accountability and auditability
7. Explicit uncertainty
8. Evaluation integrity

These principles guide the implementation and identify areas requiring further validation.

---

## 3. Human Oversight

All recommendation-oriented responses must preserve:

    human_approval_required = true
    real_action_executed = false

URAI does not autonomously:

- Disable accounts
- Isolate hosts or networks
- Modify firewall rules
- Terminate sessions
- Shut down industrial equipment
- Modify PLC, DCS, SCADA or SIS configurations
- Restore backups
- Execute recovery or startup procedures

Operational decisions remain with authorized personnel.

The presence of a dashboard approval section does not constitute authority to execute an industrial action.

---

## 4. Transparency and Explainability

URAI presents available model evidence and supporting information to analysts.

The inference architecture includes:

- Deterministic rule evidence
- Anomaly evidence
- CatBoost evidence
- Graph evidence
- Logistic stacking
- Probability calibration
- Auditable decision thresholds

Unavailable components must be identified.

The current temporal evidence component is unavailable.

The system must not invent missing model scores.

Component evidence supports investigation but does not provide a complete causal explanation of an incident.

---

## 5. Risk Score and Model Confidence

The dashboard's Attack Risk Score is derived from:

    Calibrated attack probability × 100

It represents the model's estimated attack probability under its synthetic development and calibration assumptions.

It does not measure:

- Physical safety risk
- Financial loss
- Operational downtime
- Industrial process damage
- Recovery duration
- Independently established model reliability

Model confidence has not been independently established.

The dashboard must not present calibrated probability as a separate validated confidence metric.

---

## 6. Evidence Provenance

URAI distinguishes different evidence sources and runtime states.

Relevant provenance categories include:

- LIVE_MODEL
- SYNTHETIC_GROUND_TRUTH
- STATIC_SCENARIO_METADATA
- DERIVED_BY_BACKEND
- FALLBACK
- UNAVAILABLE

Synthetic ground truth must not enter deployed inference inputs.

Fallback evidence must not be presented as live-model success.

Unavailable evidence must remain visibly unavailable.

---

## 7. Fail-Closed Behavior

Missing, corrupt, stale or incompatible required artifacts must not silently produce a normal decision.

The system must preserve warnings and communicate degraded or unavailable conditions.

This prevents missing model evidence from being disguised as a successful low-risk assessment.

A normal decision does not guarantee the absence of an attack.

---

## 8. Synthetic Data Limitations

The project uses synthetic defensive scenarios.

Synthetic data supports controlled testing, repeatability and development without executing real ransomware.

However, synthetic datasets may not reproduce:

- Real attacker behavior
- Complex industrial-network conditions
- Changing operational baselines
- Real-world class imbalance
- Organization-specific security practices
- Unanticipated failure modes

Therefore, synthetic evaluation results cannot establish production performance.

---

## 9. Evaluation Integrity

Training, validation, calibration and holdout populations must remain governed by declared separation rules.

Synthetic scenario truth must remain separate from observable inference features.

Final holdout data must not be used to tune the model or thresholds within the same evaluation cycle.

Previously observed holdout failures must remain recorded.

A future evaluation cycle requires a newly established and sealed holdout boundary.

---

## 10. Recorded Detection-Quality Limitations

Recorded holdout evaluations failed mandatory detection-quality acceptance gates.

Known concerns include:

- Insufficient precision
- False-positive rates requiring improvement in development evaluation
- Inadequate attack recall
- Missed synthetic attack scenarios
- Limited evidence of generalization

The October 5 frozen holdout scored 20 scenarios (4 attacks and 16 non-attacks).
It recorded TP=0, TN=16, FP=0 and FN=4, with attack recall 0%,
precision 0% and false-positive rate 0%.

Separately, Cycle 2 development evaluation recorded investigate-or-higher
recall of 75%, high-risk recall of 12.5%, and benign false-positive rate
of 46.43%. These development results must not be treated as independent
holdout performance.

A recorded synthetic petrochemical attack received a normal model decision.

This is an important false-negative example.

It demonstrates that the system must not be treated as a reliable standalone industrial attack detector.

The current model is not production-ready.

---

## 11. Calibration Limitations

Cycle 2 development evidence recorded improvements in calibration metrics:

| Metric | Before calibration | After calibration |
|---|---:|---:|
| Brier score | 0.2653 | 0.2340 |
| Log loss | 0.7357 | 0.6606 |
| Expected Calibration Error | 0.1847 | 0.1315 |

These are development/calibration results.

They do not establish improved independent holdout detection performance.

Calibration improvement must not be described as proof of improved attack detection.

---

## 12. Data Drift Monitoring

The RW-130-1 prototype calculates Population Stability Index across 54 features.

The recorded offline synthetic development comparison flagged two features above the declared PSI threshold.

This supports inspection of feature-distribution differences.

It does not establish:

- Live data drift
- Continuous production monitoring
- Chronological population drift
- Automatic model retraining

The dashboard explicitly labels the results as offline synthetic evidence.

---

## 13. Model Drift

An offline model-drift comparison prototype exists.

Operational model drift requires independently evaluated, comparable chronological populations.

Such evidence is not currently available.

Therefore, operational model drift remains unavailable.

Data drift must not be reported as proof of model drift.

---

## 14. Incident Timing Limitations

The RW-130-3 calculator supports:

- Mean Time to Detect
- Mean Response Time
- Mean Recovery Time

The calculator has automated test coverage.

However, no independently verified incident timestamp dataset is connected to the dashboard.

Operational MTTD and response/recovery metrics remain unavailable.

Test-fixture values must not be reported as operational performance.

The intended meaning of MTTR must be agreed before presenting that abbreviation as a measured metric.

---

## 15. Forensic Analysis Limitations

URAI provides preliminary forensic evidence presentation and offline event summarization.

These capabilities do not establish:

- Complete forensic reconstruction
- Verified attacker attribution
- Complete chain of custody
- Confirmed incident root cause
- Verified affected-asset inventory
- Confirmed industrial consequences

Human investigation and independent evidence remain necessary.

---

## 16. Industrial Safety Boundary

Cybersecurity evidence and physical safety determinations must remain separate.

URAI cannot independently determine:

- Process safety
- Equipment integrity
- Emergency shutdown requirements
- Industrial operating conditions
- Personnel safety
- Recovery or startup authorization

Industrial consequences require assessment by authorized operations and safety personnel.

The system must not transform a cyberattack probability into a physical-safety claim.

---

## 17. Missing Canonical Runtime Capabilities

The current canonical API does not fully provide:

- Verified incident-stage reconstruction
- Complete incident timeline
- Full affected-asset localization
- Confirmed propagation paths
- Complete recovery-readiness evidence
- Operational MTTD and MTTR
- Independently validated model confidence

Dashboard sections representing these areas must preserve unavailable states when evidence is missing.

---

## 18. Reliability and Testing Evidence

The following implementation checks passed during review preparation:

| Area | Result |
|---|---|
| Frontend production build | Passed |
| TypeScript compilation | Passed |
| ESLint | Passed |
| Frontend regression tests | 51/51 |
| Backend monitoring endpoint tests | 5/5 |
| Incident timing calculator tests | 14/14 |
| Promoted Cycle 2 artifact integrity | 12/12 |
| Data Drift dashboard inspection | Passed |
| Incident Metrics dashboard inspection | Passed |

These results demonstrate specific implementation correctness properties.

They do not override failed detection-quality gates.

Passing software tests is not equivalent to demonstrating operational model reliability.

---

## 19. Accountability and Auditability

The system preserves available:

- Request identifiers
- Trace identifiers
- Model decisions
- Component evidence
- Artifact provenance
- Warnings
- Safety fields
- Review-related information

These support investigation and technical review.

The prototype does not establish a complete enterprise audit or regulatory compliance program.

---

## 20. Responsible AI Risk Register

| Risk | Current treatment | Remaining limitation |
|---|---|---|
| False-negative detection | Recorded evaluation and visible warnings | Detection quality gates failed |
| False-positive alerts | Threshold evaluation and reporting | False-positive rate remains concerning |
| Missing model evidence | Explicit unavailable states | Some capabilities unavailable |
| Synthetic-to-real generalization | Synthetic-only scope disclosure | No field validation |
| Automation-related harm | Human approval and non-execution | Requires organizational controls in deployment |
| Misleading confidence | Separate risk-score interpretation | Independent confidence unavailable |
| Data drift | Offline PSI monitoring | No live chronological monitoring |
| Model drift | Offline comparator prototype | No operational drift measurement |
| Misleading response metrics | Explicit unavailable timing states | No verified incident timestamps |
| Physical safety misinterpretation | Separate cyber and operational boundaries | Requires qualified human assessment |
| Evaluation leakage | Holdout separation and freeze rules | Future cycles require renewed evaluation |

---

## 21. Future Validation Requirements

Before any production deployment could be considered, future work would require:

1. Improved detection quality on independently sealed evaluation data.
2. Stronger petrochemical-sector performance.
3. Evaluation using appropriately governed real-world evidence.
4. Independent validation of calibration and confidence claims.
5. Chronological data-drift and model-drift monitoring.
6. Verified incident timestamp collection.
7. Operationally meaningful MTTD and response/recovery measurements.
8. Complete runtime evidence contracts for required incident context.
9. Security and reliability testing under representative operating conditions.
10. Formal review by cybersecurity, OT, operations and safety stakeholders.

These are future requirements, not completed project capabilities.

---

## 22. Final Responsible AI Statement

URAI is an integrated defensive synthetic ransomware-resilience decision-support prototype.

Its current implementation demonstrates controlled inference, evidence presentation, offline monitoring and human-approval safeguards.

The system retains known detection-quality failures and explicitly identifies unavailable evidence.

**URAI is not production-ready and must not be used to autonomously control or protect live industrial systems.**
