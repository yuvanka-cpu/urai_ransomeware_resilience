# Observable and Truth Separation

Synthetic ransomware datasets maintain a strict separation between observable
telemetry and scenario truth.

## Observable data

Observable telemetry represents what a detector could observe:

- identity events
- endpoint/process events
- file events
- network events
- backup events
- service-health events
- synthetic lifecycle and impact indicators

Observable records must not directly expose scenario labels or ground-truth
blast-radius information.

## Truth data

Ground truth is stored separately under:

- `truth/scenario/`
- `truth/affected_assets/`
- `truth/blast_radius/`
- `truth/stage/`
- `truth/recovery_order/`

Truth files are evaluation metadata and are not detector input.

## Safety

Truth and observable datasets contain synthetic information only.

No truth record authorizes or executes an operational action.
