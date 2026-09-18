# Ransomware Offline Parquet Schema Parity

## Purpose

Offline ransomware event data MUST use the same canonical field definitions,
field meanings and declared units as the online canonical event envelope.

## Canonical schema source

The canonical event schema is:

`config/ransomware/shared/schemas/canonical_event.avsc`

Offline serialization MUST NOT introduce source-native field names or alternate
meanings for canonical fields.

## Required parity

The offline Parquet representation MUST preserve:

- event_id
- event_time
- ingest_time
- schema_version
- source_system
- event_family
- event_type
- industry
- site_id
- asset_id
- zone
- actor_id
- severity
- attributes
- metrics
- quality_flags
- data_provenance
- payload_hash

## Units

Offline data MUST use the same canonical units as the online path.

A unit change is a schema evolution event and MUST follow the schema evolution
contract.

## Validation

A schema parity check MUST verify:

1. every canonical field is represented;
2. canonical field meanings are unchanged;
3. canonical units are unchanged;
4. no source-native field bypasses normalization;
5. offline and online definitions remain aligned.

## Snapshot

A canonical event Parquet snapshot MUST be generated from normalized
canonical events and accompanied by a schema parity report.

## Safety boundary

Offline serialization is for reproducible analysis and validation.

It does not authorize OT writes, account disabling, isolation, encryption,
malware execution or recovery execution.
