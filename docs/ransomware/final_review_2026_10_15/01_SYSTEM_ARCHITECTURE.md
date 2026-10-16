# URAI — System Architecture
Review: 15 October 2026
Status: Synthetic defensive proof of concept; not production-ready.

## Purpose
URAI supports investigation of ransomware-related cybersecurity evidence in energy and petrochemical environments.

## Architecture
Synthetic evidence -> React/TypeScript frontend -> FastAPI backend -> Internal ML service -> Calibrated decision -> Analyst dashboard.

## ML Components
- Deterministic rules
- Anomaly detection
- CatBoost classification
- Graph-based evidence
- Temporal evidence: unavailable
- Regularized logistic stacking and probability calibration

The promoted Cycle 2 bundle uses 54 observable features.

## Decisions
normal / investigate / high_risk / unavailable

Attack Risk Score = calibrated attack probability × 100.
It is not a validated operational or physical-safety risk score.

## Dashboard
Ten sections: Overview, Scenario Lab, Detection, Timeline, Spread, Recovery, Approval, Evidence & Audit, Model Monitoring, Incident Metrics.

Missing runtime evidence must be shown as unavailable.

## Monitoring
Offline PSI monitoring covers 54 synthetic features.
Operational model drift is unavailable.

Incident timing calculations exist offline, but operational MTTD and recovery metrics are unavailable.

## Safety
human_approval_required = true
real_action_executed = false

URAI performs no real containment, restoration, shutdown or industrial-control actions.

## Verification
Frontend: 51/51 regression tests passed across six test files.
TypeScript compilation, Vite production build, and ESLint passed.
Five monitoring tests and fourteen incident-timing tests were recorded separately.
Frontend, FastAPI backend, and Cycle 2 ML API returned HTTP 200 during live health checks.
The promoted rw0906_v2 bundle passed all 12 recorded file-integrity checks.

These checks establish integration and artifact consistency, not production detection quality.

## Limitations
Synthetic-only evidence, failed detection-quality gates, incomplete incident evidence and no production validation.
