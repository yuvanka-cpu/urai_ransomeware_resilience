# Ransomware Resilience Partition and Ordering Contract

## Normalized telemetry

- Topic: `ransomware.normalized.v1`
- Partition key: `site_id + asset_id`
- Events belonging to the same site and asset use the same partition key.
- Global ordering across all partitions is not guaranteed.

## Cross-source timelines

Cross-source event timelines must use:

- `event_time` as the event-time reference.
- Watermarks to account for late-arriving events.
- Correlation identifiers to associate related events across sources.

## Safety and processing boundary

- Partitioning does not imply global chronological ordering.
- Consumers must not assume arrival order equals event-time order.
- Protected OT dependencies remain read-only.
