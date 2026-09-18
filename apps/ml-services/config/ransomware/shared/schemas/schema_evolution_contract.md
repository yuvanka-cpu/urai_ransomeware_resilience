# Ransomware Schema Evolution Contract

## Purpose

This contract defines safe evolution rules for canonical ransomware event
schemas.

## Optional fields

New optional fields MUST have explicit defaults.

Existing required fields MUST NOT become optional without a reviewed
breaking-change process.

## Field meaning and units

The meaning of an existing field MUST NOT change.

The unit of an existing field MUST NOT change.

If a different meaning or unit is required, a new field or a breaking schema
version MUST be introduced.

## Breaking changes

Breaking changes MUST NOT be introduced silently.

A breaking change requires a new schema version or a new major topic/schema
version according to the schema registry policy.

Examples of breaking changes include:

- changing an existing field's meaning;
- changing an existing field's unit;
- changing an existing field's incompatible data type;
- removing a field required by existing consumers;
- changing the semantics of an existing enum value.

## Compatibility

Non-breaking additions must preserve the configured BACKWARD compatibility
contract.

Breaking changes require explicit review and compatibility testing before
acceptance.

## Tests

Schema evolution tests MUST verify:

1. optional fields have defaults;
2. existing field meanings remain unchanged;
3. existing units remain unchanged;
4. non-breaking additions preserve compatibility;
5. breaking changes are detected and require a new version.

## Safety boundary

Schema evolution controls data-contract changes only.

It does not authorize OT writes, account disabling, isolation, malware
execution, encryption or recovery execution.
