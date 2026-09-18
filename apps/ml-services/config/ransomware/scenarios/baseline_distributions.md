# Normal Baseline Distributions

The baseline generator produces synthetic, non-destructive activity.

## Event families

- identity — ordinary authentication activity
- endpoint — ordinary endpoint/process activity
- file — ordinary file activity
- network — ordinary network activity
- backup — ordinary backup activity
- service_health — ordinary OT-support service health activity

Each asset receives one event from each family per six-event baseline cycle.

Numeric values are deterministic pseudo-random values in the range 0.1 to 1.0
for the declared seed.

No baseline event performs an operational action.
