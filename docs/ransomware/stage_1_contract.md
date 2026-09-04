# Stage 1 Scope and Safety Contract

Stage 1 defines what the proof of concept must evaluate before ontology, schema, dataset or model work begins. It contains five energy and five petrochemical use cases. The catalogues and acceptance gates are machine-readable under `apps/ml-services/config/ransomware/`.

## Objective

Provide explainable, synthetic ransomware-resilience analysis for energy and petrochemical operational-support environments. The module may classify cyber incident progression, describe observable evidence, map possible support-service dependencies and rank items for accountable human review.

It must not execute containment, recovery or operational actions, and it must not infer a physical grid, plant, controller, protection or safety state from cyber telemetry.

## Controlled context

- Industries: `energy`, `petrochemical`
- Energy site types: `control_centre`, `substation`
- Petrochemical site types: `refinery`, `petrochemical_complex`
- Asset states: `confirmed_affected`, `suspected`, `potentially_exposed`, `protected`, `unknown`
- Operational impact is expressed only as dependency/support-service status and remains separate from the cyber incident stage.

## Safety boundary

Recommendations are explanatory review prompts. Every template requires human approval and records that no real action was executed. The module does not disable accounts, isolate hosts, change firewalls, restore services, start equipment, modify DCS/SIS/PLC/relay logic, or issue any operational command.

Missing visibility is represented as missing or unknown evidence. It never becomes proof of a normal, unsafe or compromised physical state.

## Acceptance rule

Each use case has measurable machine-readable gates in `acceptance_gates.json`. Energy and petrochemical results must be reported separately; pooled performance cannot conceal a sector-specific failure. Stage 1 is complete only after all ten use cases, templates, boundaries and thresholds receive domain-owner review and the tests pass from a clean checkout.
