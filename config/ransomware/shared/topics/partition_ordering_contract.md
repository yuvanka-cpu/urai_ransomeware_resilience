# Ransomware Partition Ordering Contract

## Partitioning

Normalized ransomware telemetry MUST be partitioned using:

`site_id + asset_id`

This provides deterministic site and asset locality for downstream processing.

## Ordering

Global ordering across normalized telemetry is NOT guaranteed.

Ingest order MUST NOT be treated as event chronology.

Event chronology MUST be derived from the canonical event-time semantics.

## Cross-source timeline requirements

Cross-source event timelines require:

- `event_time` for event chronology
- watermarks for event-time progress
- correlation identifiers for cross-source event association

These requirements apply when events from multiple telemetry sources are combined into an incident timeline.

## Online and offline consistency

The same ordering and chronology rules MUST be preserved across both online and offline processing semantics.

## Safety

The contract is limited to synthetic defensive analysis.

Protected OT dependencies remain read-only. No operational writes, account disabling, recovery execution, containment action, or other real-world action is authorized by this contract.

## Bounded lateness

Each partition MUST use an explicit non-negative allowed-lateness interval.

For a partition, the watermark is:

`max(event_time observed in partition) - allowed_lateness`

An event is considered late when:

`event_time < watermark`

Late events MUST remain explicitly identifiable as telemetry-quality conditions. They must not be silently treated as current-time events.

## Per-asset ordering

The partition key is `site_id + asset_id`.

Events within each partition MUST be deterministically ordered by:

1. `event_time`
2. `event_id`
3. `ingest_time`

This ordering is applied after replay deduplication.

## Replay handling

A repeated `event_id` with an identical canonical event payload MUST be deduplicated.

A repeated `event_id` with a different canonical event payload MUST be rejected as a conflicting replay.

Replay handling MUST occur before final per-partition event ordering.

These rules apply consistently to online and offline processing.

