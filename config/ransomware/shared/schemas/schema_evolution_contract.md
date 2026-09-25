# Schema Evolution Contract

## Compatibility policy

Non-breaking additions must preserve the configured BACKWARD compatibility mode.

New optional fields MUST have explicit defaults.

The meaning of an existing field MUST NOT change.

The unit of an existing field MUST NOT change.

Breaking changes MUST NOT be introduced silently.

A breaking schema change requires a new schema version.

## Required evolution checks

Automated evolution checks MUST verify that:

- non-breaking additions preserve compatibility
- breaking changes are detected and require a new version
- optional fields provide explicit defaults
- existing field meaning remains unchanged
- existing field units remain unchanged
- online and offline processing semantics remain aligned

## Topic-level evolution

A breaking schema change must be versioned rather than silently replacing the existing contract.

## Safety boundary

Schema evolution does not authorize:

- OT writes
- account disabling
- recovery execution

All such actions remain outside the synthetic ransomware-resilience processing boundary and require separate human authorization.
