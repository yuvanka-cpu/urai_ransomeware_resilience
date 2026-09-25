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
