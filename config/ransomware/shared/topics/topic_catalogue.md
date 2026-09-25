# Ransomware Topic Catalogue

## Required topics

| Topic | Purpose |
|---|---|
| `ransomware.raw.v1` | Raw synthetic telemetry ingestion |
| `ransomware.normalized.v1` | Canonically normalized telemetry |
| `ransomware.reference.v1` | Reference and enrichment data |
| `ransomware.feature-window.v1` | Derived temporal feature windows |
| `ransomware.incident-evidence.v1` | Incident evidence and analytical outputs |
| `ransomware.dlq.v1` | Invalid or rejected records |

## Normalized telemetry partitioning

The normalized topic uses:

`site_id + asset_id`

## Ordering semantics

Global event ordering is not guaranteed.

Cross-source chronology uses `event_time`, watermarks, and correlation identifiers.

Ingest order MUST NOT be treated as event chronology.

## Feature engineering boundary

Raw events are never used directly for feature engineering.

Raw telemetry must first pass through canonical normalization and validation before being eligible for downstream feature-window processing.

## Safety boundary

All topic definitions are for synthetic defensive ransomware-resilience processing.

No topic authorizes containment, OT writes, account disabling, recovery execution, or other real-world response actions.
