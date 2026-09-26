# Ransomware Resilience Feature Contract

## Contract identity

- Contract: RW-060-1
- Feature layer: observable ransomware resilience features
- Contract status: frozen
- Synthetic-only: true
- Real action executed: false
- Ground-truth leakage: prohibited

## Window semantics

The feature layer supports three window durations:

- 1 minute
- 5 minutes
- 15 minutes

Windows are sliding windows anchored at each observed event timestamp.

For an event timestamp `T` and duration `W`, the feature window is:

`T-W <= event_time <= T`

Events are ordered by `event_time` before feature extraction.

## Evidence domains

The feature layer exposes observable evidence counts for exactly these domains:

1. identity
2. endpoint
3. file
4. network
5. backup
6. service
7. asset
8. graph
9. context
10. quality

Domain membership is determined from documented observable evidence names and observable event types.

## Feature names

Each window produces:

- `window_duration_minutes`
- `event_count`
- `unique_asset_count`
- `unique_evidence_type_count`

Evidence-domain features:

- `identity_evidence_count`
- `endpoint_evidence_count`
- `file_evidence_count`
- `network_evidence_count`
- `backup_evidence_count`
- `service_evidence_count`
- `asset_evidence_count`
- `graph_evidence_count`
- `context_evidence_count`
- `quality_evidence_count`

Observable aggregate features:

- `observable_value_mean`
- `observable_value_max`

## Observable value extraction

The feature layer may consume only observable numeric values from these event attributes, in priority order:

1. `observable_value`
2. `value`
3. `activity_intensity`
4. `degradation_severity`

Boolean values are excluded from numeric aggregation.

Missing observable numeric values do not cause feature-generation failure.

## Forbidden deployed features

The following fields must never become deployed features:

- `scenario_id`
- `scenario_seed`
- `is_ransomware`
- `incident_stage_truth`
- `affected_asset_truth`
- `blast_radius_truth`
- `analyst_disposition`

Future or post-event truth fields are likewise prohibited.

## Provenance boundary

Features are derived only from:

- event timestamp
- event family
- event type
- asset identifier for aggregate cardinality
- observable event attributes

Scenario identifiers, scenario seeds, split labels and ground-truth labels are not feature inputs.

## Safety boundary

This feature layer performs offline synthetic feature extraction only.

It does not:

- execute containment
- modify endpoints
- modify network configuration
- modify industrial control systems
- modify backup systems
- trigger recovery actions
- execute real ransomware activity

## Acceptance criteria

RW-060-1 passes when:

1. 1-minute windows are supported.
2. 5-minute windows are supported.
3. 15-minute windows are supported.
4. All ten required evidence domains are represented.
5. Feature extraction is deterministic for identical input events.
6. Unsupported window durations are rejected.
7. Ground-truth fields are absent from deployed feature output.
8. Focused RW-060-1 tests pass.
9. The feature contract remains synchronized with the implementation.
