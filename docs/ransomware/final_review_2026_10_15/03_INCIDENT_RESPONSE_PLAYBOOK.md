# URAI — Ransomware Incident Response Playbook

**Review date:** 15 October 2026
**Project:** Energy & Petrochemical Ransomware Resilience
**Development context:** SPECTRA AI internship
**Status:** Defensive synthetic PoC; not an approved operational procedure

## 1. Purpose

This playbook explains how analysts should interpret URAI's ransomware-related evidence and decision outputs.

The system supports investigation, escalation and human review.

It does not execute containment, shutdown, restoration or industrial-control actions.

## 2. Intended Environment

The project considers cybersecurity risks affecting energy and petrochemical organizations.

Relevant systems may include:

- IT infrastructure and identity systems
- Engineering workstations
- SCADA environments
- Programmable Logic Controllers (PLCs)
- Distributed Control Systems (DCS)
- Safety Instrumented Systems (SIS)
- Operational support services

Cybersecurity indicators do not independently establish physical-safety consequences.

## 3. Response Roles

| Role | Responsibility |
|---|---|
| SOC Analyst | Review alerts and available evidence |
| SOC Lead | Coordinate cybersecurity escalation |
| Incident Commander | Coordinate authorized response |
| OT Security Specialist | Assess OT cybersecurity concerns |
| Operations Engineer | Assess operational dependencies |
| Safety Authority | Determine physical-safety requirements |
| Recovery Team | Evaluate authorized recovery procedures |

URAI does not replace these roles.

## 4. Decision Handling

### NORMAL

Meaning: The model probability is below the investigation threshold.

Analyst response:

1. Review available evidence and warnings.
2. Confirm whether any model components are missing.
3. Continue authorized monitoring.
4. Consider independent alerts and observations.

A normal decision does not prove that no attack exists.

### INVESTIGATE

Meaning: The model probability meets the investigation threshold.

Analyst response:

1. Review scenario and trace identifiers.
2. Examine rule, anomaly, CatBoost and graph evidence.
3. Identify unavailable components.
4. Examine possible credential misuse and lateral movement.
5. Seek independent verification.
6. Escalate according to organizational procedures.

No automatic containment is authorized.

### HIGH_RISK

Meaning: The model probability meets the high-risk threshold.

Analyst response:

1. Prioritize human investigation.
2. Preserve available evidence and provenance.
3. Notify authorized incident response personnel.
4. Consult OT security and operations specialists if relevant.
5. Evaluate operational dependencies separately.
6. Record human review and escalation decisions.

A high-risk result does not authorize industrial shutdown.

### UNAVAILABLE

Meaning: Required model evidence or artifacts cannot support a valid decision.

Analyst response:

1. Preserve the unavailable state.
2. Review dependency and artifact warnings.
3. Investigate using independent authorized tools.
4. Escalate significant monitoring gaps.
5. Do not interpret unavailable as normal.

Silent fallback to a successful normal decision is prohibited.

## 5. Investigation Stages

The project defines these conceptual incident stages:

1. `none`
2. `precursor`
3. `credential_misuse`
4. `lateral_movement`
5. `staging`
6. `encryption_impact`
7. `recovery`

Not all stages are exposed as verified fields by the current canonical runtime.

Unavailable incident-stage evidence must not be presented as confirmed.

## 6. Credential Misuse Investigation

Analysts may examine:

- Unusual authentication patterns
- Unexpected account activity
- Suspicious privilege-related indicators
- Supporting rule and anomaly evidence
- Missing or contradictory observations

A model score alone does not establish credential compromise.

## 7. Lateral Movement Investigation

Analysts may examine:

- Unusual remote administration activity
- Unexpected peer relationships
- Graph evidence
- Observable connectivity changes
- Supporting evidence from authorized systems

Graph propagation evidence is not proof of actual compromise.

## 8. Staging and Encryption Indicators

The prototype can represent synthetic evidence associated with ransomware staging and encryption impact.

It does not execute real ransomware or encryption payloads.

Synthetic scenario truth remains separate from inference inputs.

## 9. OT Safety Escalation

URAI must not independently determine:

- Emergency shutdown requirements
- Equipment integrity
- Process stability
- Personnel safety
- Restoration authorization
- Industrial startup requirements

Relevant concerns must be referred to authorized operations and safety personnel.

Cybersecurity probability must not be converted into a physical-safety claim.

## 10. Evidence and Audit

Analysts should preserve available:

- Request and trace identifiers
- Scenario and sector context
- Model decision
- Calibrated attack probability
- Component scores
- Missing-component indicators
- Artifact provenance
- Warnings
- Review notes

The prototype does not establish a complete forensic chain of custody.

## 11. Forensic Review

URAI provides preliminary forensic evidence presentation and offline event summarization.

These do not establish:

- Confirmed attacker attribution
- Complete root-cause analysis
- Verified asset compromise
- Full incident reconstruction
- Confirmed industrial consequences

Independent investigation remains necessary.

## 12. Human Approval

Required safety invariants:

    human_approval_required = true
    real_action_executed = false

Conceptual workflow:

    Model decision
          |
          v
    Analyst evidence review
          |
          v
    Independent verification
          |
          v
    Authorized escalation
          |
          v
    Human decision outside URAI

The dashboard is not an operational execution interface.

## 13. Recovery Readiness

Authorized personnel may evaluate:

- Backup availability
- Backup integrity
- Recovery dependencies
- Asset criticality
- Restoration sequencing
- Operational and safety constraints

The current runtime does not provide complete verified recovery context.

URAI does not execute recovery, restoration, failover or startup.

## 14. Incident Timing

The offline calculator supports:

| Metric | Definition |
|---|---|
| MTTD | Incident onset to detection |
| Mean Response Time | Detection to response initiation |
| Mean Recovery Time | Incident onset to completed recovery |

No independently verified operational incident timestamp dataset is connected.

The dashboard correctly reports these metrics as unavailable.

MTTR terminology must be agreed before presenting a measured MTTR value.

## 15. Drift Monitoring

Offline PSI monitoring is available for synthetic development populations.

Operational data drift and model drift are not established.

These monitoring results must not be described as live production evidence.

## 16. Known Detection Limitations

Recorded holdout evaluations failed mandatory detection-quality gates.

A synthetic petrochemical attack scenario received a normal decision.

Therefore:

- Normal does not guarantee benign activity.
- High risk does not confirm compromise.
- Unavailable does not mean safe.
- Model output must not replace independent investigation.

## 17. Analyst Review Checklist

- [ ] Review the model decision.
- [ ] Inspect warnings and provenance.
- [ ] Check missing evidence components.
- [ ] Preserve available audit identifiers.
- [ ] Separate cyber evidence from physical-safety claims.
- [ ] Request independent verification.
- [ ] Escalate through authorized personnel.
- [ ] Confirm human approval requirements.
- [ ] Do not execute actions through URAI.
- [ ] Record limitations and unavailable metrics.

## 18. Final Playbook Status

This playbook supports controlled demonstration of analyst decision-making.

It does not replace an organization's approved incident response procedures.

**URAI is a defensive synthetic decision-support prototype, not an autonomous industrial response system.**
