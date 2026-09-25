# Schema Registry Policy

## Key and value schemas

Key schema defines the identity and partitioning fields used to route records.

Value schema defines the canonical telemetry payload and its validation contract.

Key and value schemas are governed separately but must remain compatible with the canonical event contract.

## Compatibility

Default compatibility mode: `BACKWARD`.

`FULL` compatibility requires explicit justification and automated tests.

Compatibility checks MUST run before an updated schema is accepted.

## Breaking changes

Breaking changes require a new schema version or a new major topic version.

Breaking changes must not silently replace an existing schema contract.

## Safety

Schema registry policy applies only to synthetic defensive ransomware-resilience telemetry and does not authorize real operational actions.
