# Deterministic Rule Output Contract

## Contract identity

- Ruleset version: `1.0`
- Status: frozen
- Scope: RW-070 deterministic evidence rules
- Synthetic-only: true
- Real action executed: false

## Output fields

Each rule evaluation MUST emit exactly these fields:

- `rule_id`
- `version`
- `triggered`
- `evidence_count`
- `explanation`
- `inputs`

Field meanings:

- `rule_id` identifies the named deterministic rule.
- `version` identifies the version of the rule definition.
- `triggered` indicates whether the rule's predeclared evidence condition was observed.
- `evidence_count` reports the count of supporting observable conditions.
- `explanation` describes the observed or absent evidence condition.
- `inputs` identifies the observable feature inputs evaluated by the rule.

## Decision separation

Rule output MUST NOT emit or assign:

- `decision`
- `severity`
- `confidence`
- `action`
- `recommended_action`
- `containment`
- `recovery_action`

The rule layer provides evidence only.

Final policy, fusion, calibration and decision selection remain separate layers.

A rule being triggered MUST NOT by itself produce `high_risk` or any other final incident decision.

## Determinism

Identical feature inputs MUST produce identical rule outputs.

Missing required feature inputs MUST fail explicitly rather than silently defaulting.

Unknown rule identifiers MUST be rejected.

## Safety boundary

The rules are limited to synthetic defensive analysis.

No account disabling, containment, endpoint modification, network modification,
OT/protection-system write, recovery execution or other real-world action is
authorized by the rule layer.
