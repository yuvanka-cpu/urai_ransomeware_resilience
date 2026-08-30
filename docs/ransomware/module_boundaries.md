# URAI Ransomware Resilience — Internal Module Boundaries

**Status:** Stage 0 planning contract
**Scope:** Energy & Petrochemical Ransomware Resilience Synthetic PoC

## Runtime flow

```text
Browser → Backend API → Internal ML service
```

The browser never calls the ML service directly. The backend is the orchestration boundary and must preserve decisions, provenance, warnings and safety fields returned by controlled downstream services.

## Backend

**Root:** `apps/backend/`
**Stage 0 status:** Foundation implemented; controller, policy and audit directories are skeletons.

Responsibilities include request validation, contract enforcement, later ML-service orchestration, recommendation assembly, request/trace correlation and visible degraded/unavailable behavior. It must not execute containment, recovery or operational-control actions, independently replace an ML decision, or present fallback content as live inference.

## ML service

**Root:** `apps/ml-services/`
**Status:** Planned skeleton; not implemented in Stage 0.

Later responsibilities include feature-contract validation, deterministic rules, artifact validation, inference, calibration, threshold policy and a canonical internal ransomware result. Missing, stale, corrupt or incompatible artifacts must produce visible degraded or unavailable behavior.

## Frontend

**Root:** `apps/frontend/`
**Status:** Planned skeleton; not implemented in Stage 0.

The dashboard will present scenario context, decisions, evidence, provenance, warnings, unavailable/fallback states and human-review records. It must not suppress mandatory warnings, duplicate decision rules, call the ML service directly or make recommendations executable.

## Synthetic data

**Root:** `data/synthetic/ransomware_poc/`
**Status:** Planned skeleton; generation begins at Stage 4 after Stages 0–3 pass.

Observable telemetry, static scenario metadata and synthetic truth must remain physically and contractually separate. Synthetic truth must never be accepted as inference input. Complete scenario IDs and seeds will be grouped across train, validation, calibration, test and untouched holdout splits.

## Configuration

**Root:** `apps/ml-services/config/ransomware/`
**Status:** Planned skeleton; governed contracts begin in Stage 1.

Configuration will hold sector, use-case, decision, safety, feature, model, artifact and acceptance-gate values. It must not contain executable operational actions.

## Artifacts

**Root:** `artifacts/`
**Status:** Planned skeleton; not implemented in Stage 0.

Later model, calibration and evaluation artifacts must be versioned, checksummed and accompanied by manifests. Required artifact failure must never silently produce a normal decision.

## Cross-module invariants

- `human_approval_required` is always `true`.
- `real_action_executed` is always `false`.
- Fallback is labelled `FALLBACK` and unavailable is distinct from success.
- Cyber incident stage remains separate from operational consequence.
- Protected OT and safety dependencies are context only; no commands are sent.
- No module executes malware, encryption, destructive behavior, operational containment, recovery, restore, startup or control actions.
