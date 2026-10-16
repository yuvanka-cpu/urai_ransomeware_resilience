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

## RW-060-2 — Identity feature extensions

Status: frozen after implementation and test validation.

Identity features added to the observable window contract:

- `auth_failure_count`
- `distinct_source_host_count`
- `new_source_relationship_count`
- `privilege_change_count`

All four features are computed exclusively from observable event attributes inside the event-time window.

### Window semantics

- Supported windows: 1, 5 and 15 minutes.
- Window interval: `[T-W, T]`.
- Both start and end boundaries are inclusive.
- Events outside the selected event-time window are excluded.
- Distinct source hosts are counted from the observable `source_host` attribute.
- Authentication failures are counted from observable `auth_failure=true`.
- New source relationships are counted from observable `new_source_relationship=true`.
- Privilege changes are counted from observable `privilege_change=true`.

### Leakage boundary

These identity features do not use:

- scenario identifiers
- scenario seeds
- ransomware ground truth
- incident-stage truth
- affected-asset truth
- blast-radius truth
- analyst disposition

The features therefore remain suitable for leakage-safe offline/online feature computation.

### RW-060-2 acceptance evidence

- Manual 1-minute identity window test: passed.
- Manual 5-minute boundary test: passed.
- Event-outside-window test: passed.
- Full ransomware test suite: 227 passed.
- Synthetic-only processing: true.
- Real operational action executed: false.

## RW-060-3 — Endpoint and file feature extensions

Status: frozen after implementation and test validation.

Endpoint features:

- `rare_process_chain_score`
- `unsigned_burst_count`
- `task_service_creation_count`

File features:

- `write_rate`
- `rename_rate`
- `extension_change_ratio`
- `entropy_proxy`

### Window semantics

- Supported windows: 1, 5 and 15 minutes.
- Window interval: `[T-W, T]`.
- Both start and end boundaries are inclusive.
- Write and rename rates are calculated over the selected window duration.
- Extension-change ratio is calculated as extension-change events divided by file events.
- Entropy proxy is calculated from observable entropy-proxy values.
- Rare process-chain score is the proportion of window events explicitly marked as rare process-chain activity.
- Unsigned burst and task/service creation are counted from observable boolean attributes.

### Leakage boundary

These features use only observable event attributes and do not use:

- scenario identifiers
- scenario seeds
- ransomware ground truth
- incident-stage truth
- affected-asset truth
- blast-radius truth
- analyst disposition

### RW-060-3 acceptance evidence

- Manual endpoint/file feature test: passed.
- Five-minute window boundary test: passed.
- Outside-window exclusion test: passed.
- Focused feature tests: 11 passed.
- Full ransomware test suite: 230 passed.
- Synthetic-only processing: true.
- Real operational action executed: false.

## RW-060-4 — Network, backup, service and quality window features

Status: frozen

Supported windows: 1, 5 and 15 minutes.

Window semantics: `[T-W, T]`, inclusive of both boundaries.

Network features:
- `remote_admin_peer_count`
- `new_peer_ratio`
- `zone_crossing_count`
- `outbound_bytes`

Backup features:
- `backup_age_minutes`
- `backup_failure_streak`
- `immutable_copy_present_count`
- `restore_test_age_days`

Service features:
- `service_availability_ratio`

Quality features:
- `ingestion_lag_seconds`
- `stale_data_ratio`

All features are derived only from observable event attributes inside the selected event-time window.

Service availability ratio uses only events containing `service_available` evidence.

Stale-data ratio uses only events containing `stale_data` evidence.

No scenario truth, labels, future events, or deployment-forbidden fields are used.

Focused RW-060-4 tests: 14 passed.

Synthetic-only evidence: yes.

Real action executed: false.

## RW-060-5 — Graph, context and quality window features

Status: frozen

Supported windows: 1, 5 and 15 minutes.

Window semantics: `[T-W, T]`, inclusive of both boundaries.

Graph and asset features:
- `criticality_score`
- `recovery_tier`
- `protected_boundary_hops`
- `critical_service_exposure_count`

Context features:
- `maintenance_approval_ratio`

Quality features:
- `missing_source_mask`
- `late_event_ratio`
- `stage_transition_score`

Definitions:
- `criticality_score` is the maximum observable criticality score inside the selected window.
- `recovery_tier` is the maximum observable recovery tier inside the selected window.
- `protected_boundary_hops` is the sum of observable protected-boundary hops inside the selected window.
- `critical_service_exposure_count` counts observable events marked as critical-service exposure.
- `maintenance_approval_ratio` is the proportion of window events explicitly marked as maintenance approved.
- `missing_source_mask` counts observable events explicitly marked as missing-source evidence.
- `late_event_ratio` is the proportion of window events explicitly marked as late events.
- `stage_transition_score` is the mean observable stage-transition score inside the selected window.

All features are derived only from observable event attributes inside the selected event-time window.

Protected-boundary metadata itself is not used directly as a deployed feature; only explicit observable boundary-hop evidence is used.

No scenario truth, labels, future events, or deployment-forbidden fields are used.

Focused RW-060-5 tests: 16 passed.

Synthetic-only evidence: yes.

Real action executed: false.

## RW-060-6 — Energy-sector feature extensions

Status: frozen

Supported windows: 1, 5 and 15 minutes.

Window semantics: `[T-W, T]`, inclusive of both boundaries.

Energy features:
- `scada_visibility_ratio`
- `substation_support_exposure_count`
- `relay_management_adjacency_count`
- `communications_health_ratio`

Definitions:
- `scada_visibility_ratio` measures the proportion of applicable SCADA visibility evidence events carrying explicit observable availability evidence.
- `substation_support_exposure_count` counts observable remote-session, zone-transition, protected-boundary and communications evidence associated with substation-support exposure.
- `relay_management_adjacency_count` counts observable configuration, repository, maintenance and protected-boundary evidence associated with relay-management adjacency.
- `communications_health_ratio` measures the proportion of applicable communications evidence events carrying explicit observable communications availability evidence.

All features use observable event attributes and event-time windows only.

Missing applicable evidence produces an explicit zero value and does not establish physical grid state.

No relay interrogation, RTU/IED write, SCADA command, dispatch action, firewall change, isolation or other operational action is executed.

No scenario truth, labels, future events or deployment-forbidden fields are used.

Synthetic-only evidence: yes.

Real action executed: false.
## RW-060-7 — Petrochemical-sector feature extensions

Status: frozen

Supported windows: 1, 5 and 15 minutes.

Window semantics: `[T-W, T]`, inclusive of both boundaries.

Petrochemical features:
- `dcs_support_exposure_count`
- `alarm_support_health_ratio`
- `sis_esd_adjacency_count`
- `batch_quality_dependency_exposure_count`

Definitions:
- `dcs_support_exposure_count` counts observable DCS and engineering-support evidence inside the selected event-time window, including project-file, process, signer, remote-session, service, configuration, maintenance, zone-path and backup-coverage evidence.
- `alarm_support_health_ratio` measures the proportion of applicable alarm-support availability evidence carrying explicit observable service availability.
- `sis_esd_adjacency_count` counts observable engineering, authorization, service, communications, protected-zone and proof-test evidence associated with SIS/ESD boundary adjacency.
- `batch_quality_dependency_exposure_count` counts observable ingestion, records, batch-event, file, service, database, communications and campaign/correlation evidence associated with batch and quality-system dependencies.

All features use observable event attributes and event-time windows only.

Missing applicable evidence produces an explicit zero value and does not establish physical process state, product quality, SIS/ESD state or plant safety.

No controller query or write, DCS/HMI restart, logic change, process action, SIS/ESD interrogation, bypass, reset, logic download, alarm change, batch decision, quality release or loading action is executed.

No scenario truth, labels, future events or deployment-forbidden fields are used.

Synthetic-only evidence: yes.

Real action executed: false.

## RW-060-9 — Offline/online feature parity

Status: frozen

Offline and online feature paths MUST use the same observable feature
definitions and the same event-time window semantics.

Canonical events are replayed through both paths using identical event
content.

The offline path applies deterministic event-time ordering.

The online path applies partition-aware event-time ordering, bounded
lateness and replay deduplication before invoking the shared feature
extractor.

Every produced feature field MUST be compared between the offline and online
paths.

Declared comparison tolerance: `1e-9`.

A parity run passes only when:

- 100% of feature fields are compared;
- no unexplained mismatch remains;
- identical canonical-event replays do not change feature values;
- conflicting replays are rejected;
- missing feature fields are treated as parity failures.

No separate training/runtime feature formula is permitted.

Synthetic-only evidence: yes.

Real action executed: false.
