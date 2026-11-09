"""Deterministic illustrative background measurements for Cycle 3.

This module produces synthetic baseline values, not real industrial
measurements or empirically calibrated operating distributions.

Background values depend on sector, asset, use case, observation minute,
and evidence type. They do not depend on scenario variant, scenario ID,
scenario seed, or dataset split.

Do not use these measurements for model training until downstream
semantic, temporal, leakage, and quality audits are completed.
"""

import hashlib
import random
from dataclasses import dataclass

from config.ransomware.scenarios.cycle3_measurement_profile import (
    build_cycle3_measurement_profile,
)
from config.ransomware.scenarios.cycle3_measurement_seed import (
    build_cycle3_measurement_seed,
)
from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    require_cycle3_measurement_value,
)
from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    get_cycle3_evidence_definition,
)


BACKGROUND_STREAM_NAMESPACE = "urai-cycle3-background-v1"


@dataclass(frozen=True)
class Cycle3BackgroundMeasurement:
    """One validated synthetic background measurement."""

    observation_minute: int
    event_type: str
    measured_value: int | float | bool
    unit: str | None


def _background_stream_seed(
    *,
    measurement_seed: int,
    observation_minute: int,
    event_type: str,
) -> int:
    """Derive a separate deterministic stream for one observation."""

    components = (
        BACKGROUND_STREAM_NAMESPACE,
        str(measurement_seed),
        str(observation_minute),
        event_type,
    )

    material = "".join(
        f"{len(component)}:{component}"
        for component in components
    )

    digest = hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()

    return int(digest[:16], 16)


def build_cycle3_background_measurements(
    *,
    base_seed: int,
    sector: str,
    asset_id: str,
    use_case_id: str,
) -> tuple[Cycle3BackgroundMeasurement, ...]:
    """Build the same background schedule for all scenario variants."""

    profile = build_cycle3_measurement_profile()

    measurement_seed = build_cycle3_measurement_seed(
        base_seed=base_seed,
        sector=sector,
        asset_id=asset_id,
        use_case_id=use_case_id,
    )

    observations = []

    for minute in profile.observation_minutes:
        for event_type in profile.event_types:
            definition = get_cycle3_evidence_definition(event_type)

            stream_seed = _background_stream_seed(
                measurement_seed=measurement_seed,
                observation_minute=minute,
                event_type=event_type,
            )

            rng = random.Random(stream_seed)

            if event_type == "privilege_change_activity":
                value = rng.random() < 0.05

            elif event_type == "file_write_activity":
                value = rng.randint(0, 12)

            elif event_type == "file_rename_activity":
                value = rng.randint(0, 4)

            elif event_type == "service_state_observation":
                value = rng.random() >= 0.02

            elif event_type == "telemetry_freshness_observation":
                value = round(rng.uniform(0.0, 5.0), 3)

            else:
                raise ValueError(
                    f"Unsupported background evidence: {event_type}"
                )

            validated_value = require_cycle3_measurement_value(
                event_type,
                value,
            )

            observations.append(
                Cycle3BackgroundMeasurement(
                    observation_minute=minute,
                    event_type=event_type,
                    measured_value=validated_value,
                    unit=definition.unit,
                )
            )

    expected_count = (
        len(profile.observation_minutes)
        * len(profile.event_types)
    )

    if len(observations) != expected_count:
        raise ValueError(
            "Incomplete background measurement schedule"
        )

    return tuple(observations)
