# Ransomware Resilience Schema Evolution Policy

## Evolution rules

1. Optional fields must have explicit defaults.
2. Existing field meaning must never be changed.
3. Existing field units must never be changed.
4. Breaking changes require a new schema version.
5. Breaking topic-level changes require a new major topic version.
6. Existing consumers must remain compatible under the registered compatibility policy.
7. New fields must not silently replace or reinterpret existing fields.

## Canonical contract

The canonical event envelope remains the source of truth for online and offline processing.

Schema evolution must preserve the same field definitions, units and semantics
across both paths.

## Validation

Schema changes must be covered by automated compatibility and evolution tests
before acceptance.
