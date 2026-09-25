# Canonical Observable Event Contract

## Purpose

This contract defines the canonical observable-event envelope used by the
URAI ransomware resilience module for normalized online and offline data.

The canonical event is created after source-specific data has been normalized.
Downstream feature engineering must use canonical fields rather than
source-native fields.

## Fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `event_id` | string | yes | Unique identifier for the observable event |
| `event_time` | string | yes | Event occurrence time in canonical UTC representation |
| `ingest_time` | string | yes | Time the event entered the canonical pipeline |
| `schema_version` | string | yes | Version of this canonical event schema |
| `source_system` | string | yes | Registered source-system category |
| `event_family` | string | yes | Registered event-family category |
| `event_type` | string | yes | Specific normalized event type |
| `industry` | string | yes | Canonical sector: energy or petrochemical |
| `site_id` | string | yes | Canonical site identifier |
| `asset_id` | string | yes | Canonical asset identifier |
| `zone` | string | yes | Canonical six-zone classification |
| `actor_id` | string or null | no | Canonical actor/account identifier when available |
| `severity` | string | yes | Canonical severity classification |
| `attributes` | map<string,string> | yes | Normalized descriptive attributes |
| `metrics` | map<string,double> | yes | Normalized numeric measurements |
| `quality_flags` | array<string> | yes | Data-quality conditions attached to the event |
| `data_provenance` | string | yes | Provenance classification for the event |
| `payload_hash` | string | yes | Deterministic hash representing the canonical payload |

## Normalization rules

- Timestamps are normalized to UTC.
- Numeric values use canonical numeric representations.
- Boolean, enum, IP, identifier and hash values are normalized before entering
  the canonical event.
- Required-field failures must not be silently repaired.
- Invalid or incompatible source data is routed to the dead-letter path.
- Existing field meaning and units must not be changed by schema evolution.
- Optional fields must have explicit defaults.
- The same canonical definitions and units are used by online and offline
  processing.

## Safety boundary

This contract represents observable telemetry and metadata only. It does not
authorize control actions, account disabling, isolation, encryption, recovery
execution, or interaction with protected OT/safety systems.

## Payload-hash specification

`payload_hash` is the lowercase hexadecimal SHA-256 digest of the canonical
event payload.

The hashed payload contains every canonical event field except `payload_hash`
itself:

- `event_id`
- `event_time`
- `ingest_time`
- `schema_version`
- `source_system`
- `event_family`
- `event_type`
- `industry`
- `site_id`
- `asset_id`
- `zone`
- `actor_id`
- `severity`
- `attributes`
- `metrics`
- `quality_flags`
- `data_provenance`

The payload is serialized as UTF-8 encoded JSON using these deterministic
rules:

- Object/map keys are sorted lexicographically.
- JSON uses compact separators with no insignificant whitespace.
- Strings use standard JSON escaping.
- `null` is represented as JSON `null`.
- `quality_flags` preserves its canonical array order.
- Numeric values are hashed in their already-normalized canonical form.
- `payload_hash` is excluded from the hashed payload.

The resulting SHA-256 digest is written as lowercase hexadecimal.

The validator may therefore recompute the digest from the canonical event and
reject an event when the supplied `payload_hash` does not match.
