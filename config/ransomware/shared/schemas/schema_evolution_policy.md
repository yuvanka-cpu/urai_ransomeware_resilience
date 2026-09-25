# Schema Evolution Policy

## Field evolution

Optional fields must have explicit defaults.

Existing field meaning must never be changed.

Existing field units must never be changed.

## Breaking changes

Breaking changes require a new schema version.

Breaking topic-level changes require a new major topic version.

Breaking changes must be detected by automated compatibility and evolution tests before adoption.

## Processing parity

The same schema semantics must be preserved across online and offline processing.

Online and offline processing must interpret the canonical schema consistently.

## Validation

Schema changes must be checked for:

- backward compatibility
- required field preservation
- default values for optional fields
- unchanged field meaning
- unchanged field units
- explicit versioning for breaking changes
- automated compatibility and evolution tests
