# Ransomware Partition and Event Ordering Contract

## Partition key

Normalized ransomware telemetry is partitioned by `site_id + asset_id`.

The partition key preserves site and asset locality for normalized telemetry processing.

## Ordering semantics

Global ordering across all partitions is not guaranteed.

Within a partition, event processing must preserve the event-time semantics defined by the canonical event contract.

Ingest order MUST NOT be treated as event chronology.

## Cross-source timelines

Cross-source timelines MUST use:

- `event_time` for event chronology.
- Watermarks for event-time progress.
- Correlation identifiers for cross-source event association.

Processing must not infer chronology solely from ingestion order.

## Safety boundary

Protected OT dependencies remain read-only.

This contract does not authorize operational writes, containment actions, account disabling, recovery execution, or other real-world response actions.
