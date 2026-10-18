"""Cycle 3 half-open feature-window adapter.

Selects events in (start_time, end_time] before invoking the existing
feature extractor.

This preserves the historical extractor while defining an explicit
Cycle 3 boundary convention.

This adapter does not validate measurement semantics or evidence
availability. Those gates must be applied separately.
"""

from datetime import datetime, timedelta, timezone
from typing import Iterable

from config.ransomware.features.window_features import (
    extract_window_features,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


def extract_cycle3_window_features(
    events: Iterable[ObservableScenarioEvent],
    *,
    end_time: datetime,
    duration_minutes: int,
) -> dict[str, float]:
    """Extract features using the Cycle 3 (start, end] convention."""

    if not isinstance(end_time, datetime):
        raise ValueError("end_time must be a datetime")

    if end_time.tzinfo is None or end_time.utcoffset() is None:
        raise ValueError("end_time must be timezone-aware")

    if type(duration_minutes) is not int or duration_minutes <= 0:
        raise ValueError("duration_minutes must be a positive integer")

    normalized_end = end_time.astimezone(timezone.utc)

    start_time = normalized_end - timedelta(
        minutes=duration_minutes
    )

    selected = []

    for event in events:
        if not isinstance(event, ObservableScenarioEvent):
            raise ValueError("Invalid observable event")

        try:
            timestamp = datetime.fromisoformat(
                event.event_time.replace("Z", "+00:00")
            )
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(
                "Invalid event timestamp"
            ) from exc

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError(
                "Event timestamp must be timezone-aware"
            )

        timestamp = timestamp.astimezone(timezone.utc)

        if start_time < timestamp <= normalized_end:
            selected.append(event)

    return extract_window_features(
        selected,
        normalized_end,
        duration_minutes,
    )
