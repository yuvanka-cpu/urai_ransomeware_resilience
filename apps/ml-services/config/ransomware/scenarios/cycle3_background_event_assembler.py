"""Assemble validated Cycle 3 background measurement events.

This module converts illustrative synthetic background measurements
into validated ObservableScenarioEvent records.

It does not generate attack effects, labels, or model predictions.
The historical scenario event assembler remains unchanged.

Scenario identifiers and split metadata are retained only for
provenance and grouping; downstream model features must exclude them.
"""

from datetime import datetime, timedelta, timezone

from config.ransomware.scenarios.cycle3_background_measurements import (
    build_cycle3_background_measurements,
)
from config.ransomware.scenarios.cycle3_measurement_profile import (
    build_cycle3_measurement_profile,
)
from config.ransomware.scenarios.cycle3_validated_event_adapter import (
    build_cycle3_validated_event,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


BACKGROUND_START_TIME = datetime(
    2026, 1, 1, 6, 0, tzinfo=timezone.utc
)


def assemble_cycle3_background_events(
    *,
    base_seed: int,
    sector: str,
    asset_id: str,
    use_case_id: str,
    scenario_id: str,
    scenario_seed: int,
    split: str,
) -> tuple[ObservableScenarioEvent, ...]:
    """Build 75 validated, regularly scheduled background events."""

    profile = build_cycle3_measurement_profile()

    measurements = build_cycle3_background_measurements(
        base_seed=base_seed,
        sector=sector,
        asset_id=asset_id,
        use_case_id=use_case_id,
    )

    expected_count = (
        len(profile.observation_minutes)
        * len(profile.event_types)
    )

    if len(measurements) != expected_count:
        raise ValueError("Incomplete background measurements")

    events = []

    for sequence_index, measurement in enumerate(measurements):
        event_time = BACKGROUND_START_TIME + timedelta(
            minutes=measurement.observation_minute
        )

        event = build_cycle3_validated_event(
            scenario_id=scenario_id,
            scenario_seed=scenario_seed,
            split=split,
            sequence_index=sequence_index,
            event_time=event_time,
            asset_id=asset_id,
            event_type=measurement.event_type,
            measured_value=measurement.measured_value,
        )

        events.append(event)

    if len(events) != expected_count:
        raise ValueError("Incomplete assembled event sequence")

    return tuple(events)
