# URAI Ransomware Resilience — Stage 0 Safety Policy

## Purpose

This project is a synthetic and defensive ransomware-resilience Proof of Concept.

The system is intended to represent observable ransomware effects and resilience information without executing destructive activity.

## Prohibited Actions

The Stage 0 PoC must not:

- execute ransomware
- create or execute encryption payloads
- download or detonate malware
- perform destructive file operations
- disable user accounts
- isolate hosts or networks
- modify firewall rules
- terminate sessions
- modify DCS, SIS, PLC, controller, or other operational systems
- execute recovery actions
- perform real containment actions
- connect recommendations to operational response controls

## Mocking Boundary

Stage 0 uses controlled synthetic responses for:

- normal
- investigate
- high-risk
- unavailable
- fallback

These responses are test fixtures and do not represent live ransomware execution or live operational decisions.

## Human Approval

All recommendation-oriented responses must require human approval.

```text
human_approval_required = true
real_action_executed = false

```

The system must never represent a recommendation as an executed action.

## Provenance

Synthetic, fallback, unavailable, and other non-live outputs must be clearly identified through the response provenance fields.

Fallback output must not be presented as live-model success.

## Degraded and Unavailable States

If required runtime artifacts, contracts, calibration, dependencies, or evidence are unavailable or invalid, the system must expose the degraded or unavailable condition rather than silently presenting a normal result.

## Stage 0 Scope

Stage 0 is limited to:

- repository and backend foundation
- API contract
- schema validation
- health checking
- safe mocked responses
- basic automated tests
- documentation

ML integration, model decisions, real containment, recovery execution, and operational actions are outside the Stage 0 scope.