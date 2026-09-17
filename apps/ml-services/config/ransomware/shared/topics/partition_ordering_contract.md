# Ransomware Partition and Ordering Contract

## Purpose

This contract defines partitioning and ordering behavior for normalized
ransomware telemetry.

## Normalized telemetry partition key

Normalized telemetry MUST be partitioned using:

`site_id + asset_id`

The partition key provides stable asset-local grouping for downstream
processing.

## Ordering

Global ordering across normalized telemetry is NOT guaranteed.

Consumers MUST NOT assume that events from different partitions arrive in
global event-time order.

## Cross-source timelines

When events from multiple sources are combined into a timeline, consumers
MUST use:

- `event_time` for event chronology
- watermarks for event-time progress
- correlation identifiers for cross-source event association

Ingest order MUST NOT be treated as event chronology.

## Contract rules

1. Every normalized event has a resolved `site_id` and `asset_id`.
2. The partition key is derived from `site_id + asset_id`.
3. Partitioning MUST NOT create a global ordering guarantee.
4. Cross-source correlation MUST use explicit correlation identifiers.
5. Event-time processing MUST account for watermarks.
6. Source ingestion order MUST NOT replace `event_time`.
7. This contract applies to both online and offline processing semantics.

## Safety boundary

Partitioning and ordering support observation, analytics and recommendation.
They do not authorize control actions against OT or safety systems.
