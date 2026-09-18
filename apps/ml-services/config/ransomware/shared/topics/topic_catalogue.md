# Ransomware Resilience Topic Catalogue

## Topic patterns

- `ransomware.raw.v1`
  - Purpose: source-native raw events before canonical normalization.
  - Key: source event identifier.
  - Retention: short-lived ingestion/replay window.
  - Access: ingestion and normalization services only.

- `ransomware.normalized.v1`
  - Purpose: canonical normalized observable events.
  - Key: `site_id + asset_id`.
  - Retention: operational telemetry window.
  - Access: normalization, feature engineering, detection and orchestration services.

- `ransomware.reference.v1`
  - Purpose: governed reference data such as asset, site, service, account and dependency metadata.
  - Key: canonical identifier.
  - Retention: until superseded by a governed version.
  - Access: reference/configuration consumers.

- `ransomware.feature-window.v1`
  - Purpose: normalized event windows prepared for downstream feature computation.
  - Key: `site_id + asset_id`.
  - Retention: processing window.
  - Access: feature and model services.

- `ransomware.incident-evidence.v1`
  - Purpose: evidence associated with ransomware-resilience incident analysis.
  - Key: incident/evidence identifier.
  - Retention: incident investigation and audit window.
  - Access: authorized backend, dashboard and audit consumers.

- `ransomware.dlq.v1`
  - Purpose: records rejected during validation or normalization.
  - Key: source `event_id`.
  - Retention: replay/remediation window.
  - Access: normalization, remediation and audit services.

## Contract rules

1. Raw events are never used directly for feature engineering.
2. Normalized telemetry is keyed by `site_id + asset_id`.
3. Global event ordering is not guaranteed.
4. Cross-source timelines use `event_time`, watermarks and correlation identifiers.
5. Topic names and keys are versioned contracts.
6. Access is restricted according to topic purpose.
7. Protected OT dependencies remain read-only and recommendation-only.
