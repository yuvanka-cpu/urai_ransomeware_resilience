# Ransomware Resilience Promoted Model Card — v1

## 1. Model identity

- **Project:** Energy & Petrochemical Ransomware Resilience Module
- **Model card version:** v1
- **Model status:** Promoted Stage 9 artifact chain
- **Data type:** Synthetic defensive ransomware-resilience scenarios
- **Synthetic-only:** Yes
- **Human approval required:** Yes
- **Real action executed:** No

## 2. Promoted model chain

The promoted Stage 9 inference chain is:

1. **CatBoost engineered-feature baseline**
2. **Regularized logistic stacking**
3. **Sector/global probability calibration**
4. **Auditable threshold policy**

The chain combines independent evidence layers rather than exposing an uncalibrated weighted average as confidence.

## 3. Evidence components

### Rules

Deterministic evidence rules provide an auditable rule score based on observable ransomware-resilience indicators.

### Anomaly baseline

The anomaly component provides observable-data anomaly evidence using the established Stage 7 anomaly baseline.

### CatBoost

The CatBoost baseline operates on the declared observable feature contract.

It provides a supervised evidence component for the ransomware decision pipeline.

### Temporal challenger

The temporal challenger was evaluated during Stage 8 but was not promoted.

The Stage 9 fusion contract therefore represents the temporal component as explicitly unavailable rather than fabricating a temporal score.

### Graph component

The promoted chain uses deterministic weighted graph propagation as the auditable graph evidence component.

The graph component does not use synthetic ground truth as a deployed feature.

## 4. Stacking model

Stage 9 uses regularized logistic stacking over component evidence.

The stacking inputs are:

- rule score
- anomaly score
- CatBoost score
- temporal score
- graph score
- rules missing indicator
- anomaly missing indicator
- CatBoost missing indicator
- temporal missing indicator
- graph missing indicator

Missing-component indicators are preserved explicitly.

Direct score averaging is not used.

## 5. Out-of-fold development evidence

Stage 9 OOF scoring used:

- 36 development scenarios
- train + validation splits only
- 108 component-score rows
- 3 observation windows per scenario
- scenario-grouped cross-validation
- zero untouched-holdout rows
- zero calibration rows

The OOF process prevents the final holdout and calibration populations from entering stacking-model fitting.

## 6. Probability calibration

Probability calibration is fitted using the dedicated calibration split.

Calibration contains:

- 10 scenarios
- 30 window-level rows
- 24 negative rows
- 6 positive rows

A global sigmoid calibrator is available.

Energy has sufficient class diversity for a sector-specific sigmoid calibrator.

Petrochemical calibration data has insufficient class diversity, so the runtime explicitly uses the global sigmoid fallback rather than fabricating a sector-specific calibration model.

### Calibration evidence

Global pre-calibration:

- Brier score: 0.25499
- Log loss: 0.70563
- ECE, 5 bins: 0.23938

Global post-calibration:

- Brier score: 0.16160
- Log loss: 0.50498
- ECE, 5 bins: 0.03838

These metrics are calibration-split development evidence and are not production-performance claims.

## 7. Decision thresholds

The Stage 9 development threshold policy defines:

- **Normal:** calibrated probability below the investigate threshold
- **Investigate:** calibrated probability at or above the investigate threshold and below the high-risk threshold
- **High risk:** calibrated probability at or above the high-risk threshold

Current development thresholds:

- Investigate: **0.239133**
- High risk: **0.294338**

The thresholds were selected from observed development scenario scores under a declared synthetic cost policy.

They were not tuned on the untouched final holdout.

## 8. Development threshold evidence

At the selected development thresholds:

- investigate-or-higher attack recall: **1.0000**
- high-risk attack recall: **0.4000**
- benign false-positive rate: **0.5000**
- declared total cost: **49.0**

These are synthetic development-policy results only.

They must not be interpreted as production detection accuracy or expected field performance.

## 9. Challenger promotion boundary

Stage 8 evaluated additional challengers.

No challenger was promoted.

Rejected candidates include:

- TCN
- compact Transformer
- GraphSAGE
- GATv2

The reasons included insufficient final-holdout evidence, calibration evidence, runtime evidence, robustness evidence, and/or required sector-specific graph evidence.

Promotion was not based on novelty or pooled accuracy alone.

## 10. Intended use

The model chain is intended for:

- defensive ransomware-resilience analysis
- synthetic scenario evaluation
- evidence fusion
- analyst-facing decision support
- dashboard/API integration
- reproducible research and engineering validation

## 11. Prohibited uses

The model chain must not be used to:

- autonomously isolate systems
- disable accounts
- shut down equipment
- initiate recovery
- authorize startup or failover
- control SCADA, DCS, SIS, ESD, relay, or other operational systems
- determine physical safety
- infer physical compromise from cyber telemetry alone
- execute malware or ransomware
- replace qualified human incident-response decisions

## 12. Unavailable behavior

The runtime explicitly represents artifact failures as unavailable.

Failure conditions include:

- missing
- corrupt
- stale
- incompatible
- slow/timeout

Silent substitution of another model or artifact is prohibited.

## 13. Known limitations

- Training and evaluation evidence is synthetic.
- Current Stage 9 threshold results are development evidence.
- The untouched final holdout was deliberately excluded from Stage 9 fitting, calibration, and threshold selection.
- Production generalization has not been established.
- Petrochemical calibration lacks sufficient class diversity for a sector-specific calibrator.
- The temporal challenger was rejected and is unavailable in the promoted fusion chain.
- Development threshold selection uses declared synthetic costs, not measured operational costs.
- Sector-specific operational validation remains required before any real deployment consideration.

## 14. Safety and governance

The model produces defensive analytical evidence and recommendations.

Every operationally relevant result requires human approval.

The model does not execute real actions.

The system must not claim:

- physical safety
- plant safety
- grid safety
- controller compromise
- relay compromise
- SIS/ESD compromise
- safe startup authorization

Loss of cyber visibility must not be interpreted as proof of unsafe physical or operational state.

## 15. Artifact lineage

The promoted Stage 9 chain is represented by:

- `rw0704_catboost_model.cbm`
- `rw0902_logistic_stacking_model.json`
- `rw0903_sector_calibrators.json`
- `rw0904_threshold_policy_report.json`

The versioned promoted bundle is:

`artifacts/ransomware/promoted/rw0906_v1/`

The bundle contains checksums, feature contract, model artifacts, calibration artifacts, threshold evidence, lineage, and library-version information.

## 16. Versioning

**Model card version:** v1

**Stage:** Stage 9

**Promotion decision:** `NO_CHALLENGER_PROMOTED`

**Promoted chain:** CatBoost → Logistic Stacking → Sector Calibration → Threshold Policy

**Status:** Documentation evidence for Stage 9
