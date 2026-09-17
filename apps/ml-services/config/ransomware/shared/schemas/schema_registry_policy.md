# Ransomware Schema Registry Policy

## Purpose

This policy defines schema registration and compatibility requirements for
the ransomware resilience event pipeline.

## Key and value schemas

Kafka key schemas and Kafka value schemas MUST be registered separately.

The key schema defines the partition/join identity of a record.

The value schema defines the canonical event or contract payload.

A change to a key schema MUST be reviewed independently from a value schema
change because key changes can affect partitioning and record association.

## Compatibility

The default compatibility mode is:

`BACKWARD`

A new schema version MUST remain compatible with the previous version under
the configured BACKWARD compatibility rules.

`FULL` compatibility may be used only when there is a documented
justification and explicit compatibility tests.

## CI enforcement

Schema changes MUST be checked in CI before acceptance.

CI checks MUST verify:

1. key and value schemas are registered separately;
2. the declared compatibility mode is valid;
3. BACKWARD compatibility is preserved by default;
4. any FULL compatibility requirement has documented justification;
5. incompatible schema changes fail validation.

## Safety boundary

Schema registry validation protects data-contract integrity.

It does not authorize control actions, OT writes, account disabling,
isolation, encryption or recovery execution.
