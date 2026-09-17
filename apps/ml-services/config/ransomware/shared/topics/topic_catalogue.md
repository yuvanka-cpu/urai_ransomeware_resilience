# Ransomware Kafka Topic Catalogue

## Purpose

This catalogue defines the Kafka topic patterns used by the ransomware
resilience pipeline. Topics separate source records, canonical normalized
events, reference data, feature windows, incident evidence, and rejected
records.

The online and offline paths must use the same canonical event definitions
and units.

## Topic catalogue

| Topic | Key | Purpose | Retention | Access |
|---|---|---|---|---|
| ransomware.raw.v1 | source_system + event_id | Immutable source-ingestion records before normalization | Short-term | Ingestion/normalization |
| ransomware.normalized.v1 | site_id + asset_id | Canonical observable events after deterministic normalization | Operational window | Detection/analytics |
| ransomware.reference.v1 | asset_id | Governed asset, zone, criticality and reference metadata | Long-term | Reference/analytics |
| ransomware.feature-window.v1 | site_id + asset_id | Derived feature-window inputs for model processing | Short-term | Feature/model services |
| ransomware.incident-evidence.v1 | incident_id + event_id | Evidence associated with an incident assessment | Long-term | Incident review/audit |
| ransomware.dlq.v1 | source_system + event_id | Records rejected because they cannot be safely normalized | Long-term | Data quality/engineering |

## Partitioning

Normalized telemetry is partitioned by:

`site_id + asset_id`

Global ordering is not guaranteed.

Cross-source timelines must use:

- `event_time`
- watermarks
- correlation identifiers

## Topic rules

1. Source-native records must not bypass normalization into downstream
   feature or incident pipelines.
2. Normalized telemetry uses the canonical event envelope.
3. DLQ records preserve rejection reason information.
4. Topic names are versioned when a breaking contract requires a new topic.
5. Retention is selected according to the purpose of each topic and must not
   be treated as a data-quality control.
6. Access is limited to the pipeline responsibility described for each topic.
7. No topic grants permission to perform control actions against protected
   OT or safety systems.

## Safety boundary

These topics support observation, analysis, recommendation and audit.

They do not authorize:

- autonomous isolation
- account disabling
- malware execution
- encryption
- recovery execution
- protected OT writes or control actions
