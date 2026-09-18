# Ransomware Resilience Schema Registry Policy

## Registration

Key schemas and value schemas are registered separately.

- Key schema defines the Kafka message key.
- Value schema defines the canonical event payload.
- Both are versioned contracts.

## Compatibility

- Default compatibility mode: `BACKWARD`.
- `FULL` compatibility requires explicit justification and automated tests.
- Breaking changes require a new schema version or a new major topic version.

## CI validation

Every schema change must verify:

1. Required fields remain compatible.
2. Existing field meaning is unchanged.
3. Existing units are unchanged.
4. Optional fields have explicit defaults.
5. Breaking changes are versioned instead of silently replacing existing contracts.
