# URAI Ransomware Resilience — Planned Internal Module Boundaries

**Status:** Stage 0 planning artifact
**Scope:** Energy & Petrochemical Ransomware Resilience Synthetic PoC
**Safety classification:** Defensive synthetic PoC; recommendation/review only

## 1. Purpose

This document defines the planned internal boundaries between the backend,
ML service, frontend, synthetic-data, configuration, artifact, and
documentation components.

These boundaries are architectural planning constraints for later stages.
Components marked **PLANNED** are intentionally not implemented during Stage 0 unless explicitly required by the stage 0 task sheet.

The browser must not call the ML service directly.

---

## 2. Backend

**Planned root:**

```text
apps/backend/

Current Stage 0 implementation:

apps/backend/app/
├── routes/
├── controllers/
├── services/
├── schemas/
├── policies/
└── audit/
```
Responsibility
Browser-facing API boundary
Request validation
API contract enforcement
Safety-policy enforcement
ML-service orchestration in later stages
Recommendation assembly
Request and trace correlation
Audit context
Safe degraded, fallback, and unavailable handling
Must not
Execute containment or recovery actions
Execute operational control actions
Replace the ML decision with an independent backend decision
Present fallback content as live-model inference

Status: IMPLEMENTED FOUNDATION / LATER-STAGE EXTENSION

## 3. ML Service

Planned root:

apps/ml-services/
Planned responsibility
Feature-contract validation
Artifact loading and validation
Model inference
Deterministic rules
Tabular, temporal, and graph model components
Calibration
Threshold policy
Internal canonical ransomware result
Explicit unavailable and degraded states
Boundary

The ML service is an internal service boundary. The frontend must never call
the ML service directly.

The backend acts as the orchestration boundary between the frontend and ML
service.

Status: PLANNED — NOT IMPLEMENTED IN STAGE 0

## 4. Frontend

Planned root:

apps/frontend/
Planned responsibility
Dashboard presentation
Scenario selection and presentation
Decision and incident-stage display
Evidence and provenance presentation
Warning visibility
Fallback, unavailable, and degraded-state presentation
Human-approval review interface
Must not
Call the ML service directly
Suppress mandatory warnings
Convert recommendations into executable actions
Modify safety or execution-control fields

Status: PLANNED — NOT IMPLEMENTED IN STAGE 0

## 5. Synthetic Data

Planned root:

data/synthetic/ransomware_poc/
Planned responsibility
Synthetic scenario definitions
Observable telemetry
Scenario manifests
Synthetic ground truth
Affected-asset truth
Blast-radius truth
Incident-stage truth
Recovery-order truth
Reproducible seeds
Train, validation, calibration, test, and holdout split artifacts
Boundary

Observable synthetic data and synthetic truth must remain separate.

Synthetic truth must never be accepted as an inference feature.

Status: PLANNED — DO NOT GENERATE DATA DURING CURRENT STAGE 0 CLOSURE

## 6. Configuration

Planned root:

apps/ml-services/config/ransomware/
Planned responsibility
Sector configuration
Energy configuration
Petrochemical configuration
Scenario and use-case configuration
Decision and safety configuration
Feature-contract configuration
Model and artifact configuration
Acceptance-gate configuration
Boundary

Configuration defines governed values and contracts; it must not contain
executable operational actions.

Status: PLANNED — PARTIAL FOUNDATION ONLY

## 7. Artifacts

Planned root:

artifacts/
Planned responsibility
Versioned model artifacts
Calibration artifacts
Artifact manifests
Checksums
Artifact metadata
Evaluation reports
Promotion and rejection records
Required artifact states
loaded
missing
stale
corrupt
incompatible
timeout
Boundary

Missing, stale, corrupt, or incompatible artifacts must produce visible
degraded or unavailable behavior rather than silent substitution.

Status: PLANNED — NOT IMPLEMENTED IN STAGE 0

## 8. Documentation

Root:

docs/ransomware/
Responsibility
Safety policy
Repository map
Module boundaries
API contracts
Task tracking
Dataset documentation
Evaluation evidence
Runtime and governance evidence

Status: ACTIVE

## 9. Cross-Module Rules
The browser communicates with the backend boundary.
The backend orchestrates the ML service.
The browser never calls the ML service directly.
API schemas are shared controlled contracts.
Synthetic truth is physically and contractually separated from observable
inference data.
Every result must expose appropriate provenance.
Fallback must be explicitly labelled as FALLBACK.
UNAVAILABLE must remain visibly distinct from successful inference.
Human approval is required for recommendations.
`real_action_executed` remains `false`.
No module may execute malware, encryption payloads, destructive behavior,
operational control, containment, or recovery actions.
## 10. Stage 0 Implementation Boundary

Stage 0 establishes contracts, safety restrictions, repository readiness,
environment reproducibility, and test controls.

The following remain intentionally unimplemented until their dependent
stages are reached:

Synthetic scenario generation
Dataset generation
Feature engineering
Model training
Model calibration
ML inference implementation
Frontend dashboard implementation
Production telemetry integration
Operational response integration

This document records planned boundaries without creating placeholder
decision logic or prematurely implementing later-stage components.