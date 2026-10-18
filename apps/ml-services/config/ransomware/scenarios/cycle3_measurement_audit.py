"""Cycle 3 measurement semantics audit.

Diagnostic only. Does not alter the frozen 54-feature contract,
historical feature extraction, model decisions, or holdout artifacts.
"""

from collections import Counter
from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


VALUE_SOURCE_PRIORITY = (
    "observable_value",
    "value",
    "activity_intensity",
    "degradation_severity",
)


@dataclass(frozen=True)
class Cycle3MeasurementAudit:
    event_count: int
    measured_event_count: int
    missing_event_count: int
    source_counts: tuple[tuple[str, int], ...]
    mixed_sources: bool
    nonfinite_value_count: int


def audit_cycle3_measurements(
    events: Iterable[ObservableScenarioEvent],
) -> Cycle3MeasurementAudit:
    """Describe numeric-value provenance without imputing missing data."""

    counts: Counter[str] = Counter()
    total = 0
    measured = 0
    missing = 0
    nonfinite = 0

    for event in events:
        total += 1
        selected_source = None
        selected_value = None

        for key in VALUE_SOURCE_PRIORITY:
            value = event.attributes.get(key)

            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                selected_source = key
                selected_value = float(value)
                break

        if selected_source is None:
            missing += 1
            counts["missing"] += 1
            continue

        counts[selected_source] += 1

        if not isfinite(selected_value):
            nonfinite += 1
            continue

        measured += 1

    present_sources = {
        source
        for source, count in counts.items()
        if source != "missing" and count > 0
    }

    return Cycle3MeasurementAudit(
        event_count=total,
        measured_event_count=measured,
        missing_event_count=missing,
        source_counts=tuple(sorted(counts.items())),
        mixed_sources=len(present_sources) > 1,
        nonfinite_value_count=nonfinite,
    )
