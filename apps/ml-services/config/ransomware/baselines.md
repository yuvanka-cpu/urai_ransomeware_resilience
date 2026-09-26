# Ransomware Anomaly Baseline Contract

## Contract identity

- Task: `RW-070-3`
- Baseline version: `1.0`
- Status: frozen
- Synthetic-only: true
- Real action executed: false

## Baseline methods

The anomaly evidence layer contains:

1. Robust univariate thresholds using median and MAD-derived scale.
2. A robust multivariate score computed from the absolute robust z-scores.
3. Isolation Forest with a fixed random seed for reproducibility.

Default parameters:

- Univariate threshold: `3.5`
- Isolation Forest estimators: `100`
- Isolation Forest contamination: `auto`
- Random state: `42`

The multivariate threshold is:

`z_threshold * sqrt(number_of_features)`

## Output boundary

The baseline emits anomaly evidence only.

It MUST NOT assign or emit:

- `decision`
- `severity`
- `confidence`
- `action`
- `recommended_action`
- `high_risk`

An Isolation Forest anomaly by itself MUST NOT produce a final incident
decision.

Policy, fusion, calibration and decision selection remain separate layers.

## Data boundary

Baseline inputs are observable feature values from the frozen feature
contract.

Scenario identifiers, scenario seeds, ransomware truth, incident-stage truth,
affected-asset truth, blast-radius truth, future fields and analyst
disposition are not permitted inputs.

## Reproducibility

Identical training data, parameters and random seed MUST produce identical
baseline outputs.

Missing required features MUST fail explicitly.

Insufficient training data MUST fail explicitly.

## Safety boundary

The baseline performs synthetic defensive analysis only.

No containment, account disabling, network change, OT/protection-system write,
recovery execution or other operational action is performed.
