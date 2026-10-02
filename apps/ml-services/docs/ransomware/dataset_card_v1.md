# Ransomware Resilience Synthetic Dataset Card — v1

## 1. Dataset identity

- **Project:** Energy & Petrochemical Ransomware Resilience Module
- **Dataset type:** Synthetic defensive ransomware-resilience scenarios
- **Dataset version:** v1
- **Synthetic-only:** Yes
- **Primary use:** Development and evaluation of ransomware-resilience detection and evidence-fusion components
- **Real operational data:** None
- **Real ransomware payloads:** None

## 2. Intended use

This dataset is intended for:

- deterministic development of ransomware-resilience detection components
- comparison of engineered and challenger detection approaches
- feature-contract validation
- calibration and threshold-policy development
- defensive dashboard and API testing
- reproducibility and regression testing

It is not intended to:

- determine physical safety of an energy or petrochemical facility
- control OT, IT, SCADA, DCS, SIS, ESD, relay, or other operational systems
- authorize containment, isolation, shutdown, restoration, or startup
- execute ransomware or other malware
- replace human incident-response decisions

## 3. Scenario population

The frozen scenario registry contains **80 deterministic synthetic scenarios**.

The versioned split assignment contains:

| Split | Scenario count |
|---|---:|
| Train | 18 |
| Validation | 18 |
| Test | 14 |
| Calibration | 10 |
| Untouched final holdout | 20 |
| **Total** | **80** |

The untouched final holdout is reserved from model development and threshold selection.

## 4. Scenario types

The synthetic scenario population includes ransomware-related attack scenarios together with benign, fault, and normal scenarios.

Observable telemetry is assembled independently from synthetic scenario ground truth.

Ground-truth information is not permitted to become a deployed model feature.

## 5. Sector coverage

The dataset represents two synthetic sector contexts:

- Energy
- Petrochemical

Sector-specific observable features are represented through the feature contract, including energy-related visibility/exposure indicators and petrochemical-related support/dependency indicators.

## 6. Observable feature contract

The deployed feature contract contains **54 observable features**.

Feature groups include:

- window and event statistics
- identity and authentication evidence
- endpoint and file evidence
- network evidence
- backup and recovery evidence
- service health
- asset and graph evidence
- context and data-quality indicators
- criticality and recovery metadata
- energy-sector observable indicators
- petrochemical-sector observable indicators
- generic observable numeric summaries

The feature contract explicitly excludes synthetic ground-truth fields and other forbidden leakage sources.

## 7. Temporal representation

Windowed observations are generated for:

- 1-minute windows
- 5-minute windows
- 15-minute windows

The same frozen scenario/event source is used to derive these observations deterministically.

## 8. Development and evaluation policy

Development model fitting uses the declared train/development population.

The Stage 9 OOF component-score process uses only the train and validation scenarios.

Calibration uses the dedicated calibration split.

Threshold selection uses development evidence and does not use the untouched final holdout.

The untouched final holdout remains excluded from Stage 9 model fitting, calibration, and threshold selection.

## 9. Calibration limitations

The calibration split contains 10 scenarios.

Energy has sufficient class diversity for a sector-specific sigmoid calibrator.

The petrochemical calibration subset does not contain both classes. Therefore, a sector-specific petrochemical calibrator is not fabricated. The runtime explicitly falls back to the global sigmoid calibration policy and records the insufficient-class-diversity condition.

## 10. Data quality and failure handling

The runtime contract explicitly handles:

- missing artifacts
- corrupt artifacts
- stale artifacts
- incompatible artifacts
- slow/timeout artifacts

These states must become visibly unavailable rather than silently substituting another model or artifact.

Missing telemetry and stale/late observations are represented through observable quality features and explicit runtime contracts.

## 11. Provenance and reproducibility

Scenario generation, event assembly, feature extraction, model artifacts, calibration artifacts, threshold policy, and promoted bundle contents are versioned and checksummed where required.

The promoted Stage 9 bundle records:

- feature contract
- model artifacts
- calibration artifacts
- threshold policy
- training/evaluation lineage
- library versions
- SHA-256 checksums

## 12. Known limitations

- The dataset is synthetic and does not establish real-world attack prevalence.
- Synthetic telemetry cannot establish production detection performance.
- Sector context is represented through synthetic observable evidence and does not constitute a model of a real facility.
- The current Stage 8 challenger evidence did not justify promotion of the temporal or learned graph challengers.
- The temporal component is therefore explicitly unavailable in the promoted Stage 9 fusion chain.
- The petrochemical calibration subset has insufficient class diversity for a sector-specific calibrator.
- Threshold costs are declared development assumptions rather than measured operational costs.
- Final production suitability requires additional independent validation, calibration, runtime, and sector-specific evidence.

## 13. Safety and governance

All outputs are defensive recommendations/evidence summaries.

The system requires human approval.

The system does not execute real operational actions.

The system does not claim physical safety, plant state, grid state, controller compromise, relay compromise, SIS/ESD compromise, or safe startup authorization.

Loss of cyber visibility must not be interpreted as proof of an unsafe physical or operational state.

## 14. Versioning

**Dataset card version:** v1

**Status:** Stage 9 documentation evidence

**Scope:** Synthetic ransomware-resilience dataset and its declared development/evaluation boundaries.

