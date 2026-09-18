# Ransomware Scenario Catalogue

Each scenario configuration is deterministic for its declared seed.

## Required fields

- `scenario_id` — unique scenario identifier.
- `seed` — deterministic generation seed.
- `industry` — energy or petrochemical.
- `site` — scenario site identifier.
- `asset_set` — canonical assets participating in the scenario.
- `lifecycle_timing` — timing parameters for scenario stages.
- `event_family_parameters` — parameters controlling generated event families.
- `intended_labels` — intended scenario labels kept separate from observable events.

## Safety boundary

Scenario configuration describes synthetic telemetry generation only.

It must not contain destructive payloads, operational commands, encryption programs,
or instructions for changing real systems or files.
