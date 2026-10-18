"""Cycle 3 synthetic event timeline adapter.

Development/calibration infrastructure only.

This module does not modify historical scenario generators,
create holdouts, train models, or execute operational actions.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


TIMELINE_START = datetime(
    2026, 1, 1, 6, 0, tzinfo=timezone.utc
)

OBSERVATION_HORIZON_MINUTES = 30


@dataclass(frozen=True)
class Cycle3Timeline:
    start_time: datetime
    observation_end: datetime
    events: tuple[ObservableScenarioEvent, ...]


def align_cycle3_timeline(
    events: list[ObservableScenarioEvent],
) -> Cycle3Timeline:
    """Align synthetic events to a common observation horizon."""

    if not events:
        raise ValueError("Cycle 3 timeline requires events")

    ordered = sorted(
        events,
        key=lambda event: event.sequence_index,
    )

    indexes = [event.sequence_index for event in ordered]

    if len(indexes) != len(set(indexes)):
        raise ValueError("Duplicate event sequence indexes")

    if indexes != list(range(len(indexes))):
        raise ValueError("Event sequence indexes must be contiguous")

    scenario_ids = {event.scenario_id for event in ordered}
    splits = {event.split for event in ordered}

    if len(scenario_ids) != 1:
        raise ValueError("Timeline cannot mix scenarios")

    if len(splits) != 1:
        raise ValueError("Timeline cannot mix splits")

    if not splits.issubset({"development", "calibration"}):
        raise ValueError("Unsupported Cycle 3 split")

    if len(ordered) > OBSERVATION_HORIZON_MINUTES + 1:
        raise ValueError("Events exceed observation horizon")

    original_times = []

    for event in ordered:
        original_time = datetime.fromisoformat(
            event.event_time.replace("Z", "+00:00")
        )

        if original_time.tzinfo is None:
            raise ValueError("Naive event timestamp")

        original_times.append(original_time)

    if any(
        current <= previous
        for previous, current in zip(
            original_times,
            original_times[1:],
        )
    ):
        raise ValueError(
            "Original event timestamps must be strictly increasing"
        )

    original_start = original_times[0]

    aligned = []

    for event, original_time in zip(ordered, original_times):
        elapsed = original_time - original_start

        if elapsed > timedelta(
            minutes=OBSERVATION_HORIZON_MINUTES
        ):
            raise ValueError(
                "Original event timeline exceeds observation horizon"
            )

        aligned_time = TIMELINE_START + elapsed

        aligned.append(
            replace(
                event,
                event_time=aligned_time.isoformat().replace(
                    "+00:00", "Z"
                ),
            )
        )

    return Cycle3Timeline(
        start_time=TIMELINE_START,
        observation_end=TIMELINE_START + timedelta(
            minutes=OBSERVATION_HORIZON_MINUTES
        ),
        events=tuple(aligned),
    )
