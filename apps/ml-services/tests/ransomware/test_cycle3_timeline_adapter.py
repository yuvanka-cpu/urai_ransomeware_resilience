"""Tests for the Cycle 3 synthetic observation timeline."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from config.ransomware.scenarios.cycle3_scenario_adapter import (
    build_cycle3_adapted_scenarios,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)
from config.ransomware.scenarios.cycle3_timeline_adapter import (
    TIMELINE_START,
    OBSERVATION_HORIZON_MINUTES,
    Cycle3Timeline,
    align_cycle3_timeline,
)


@pytest.fixture(scope="module")
def sample_events():
    batch = build_cycle3_adapted_scenarios()
    scenario = batch.scenarios[0]
    return assemble_scenario_events(scenario)


@pytest.fixture(scope="module")
def timeline(sample_events):
    return align_cycle3_timeline(sample_events)


def test_returns_timeline(timeline):
    assert isinstance(timeline, Cycle3Timeline)


def test_common_start_time(timeline):
    assert timeline.start_time == TIMELINE_START


def test_fixed_observation_end(timeline):
    assert timeline.observation_end == TIMELINE_START + timedelta(
        minutes=OBSERVATION_HORIZON_MINUTES
    )


def test_event_count_preserved(sample_events, timeline):
    assert len(timeline.events) == len(sample_events)


def test_event_order_preserved(timeline):
    assert [
        event.sequence_index for event in timeline.events
    ] == list(range(len(timeline.events)))


def test_event_timestamps_aligned(timeline):
    for event in timeline.events:
        actual = datetime.fromisoformat(
            event.event_time.replace("Z", "+00:00")
        )
        expected = TIMELINE_START + timedelta(
            minutes=event.sequence_index
        )
        assert actual == expected


def test_all_events_within_horizon(timeline):
    for event in timeline.events:
        timestamp = datetime.fromisoformat(
            event.event_time.replace("Z", "+00:00")
        )
        assert timeline.start_time <= timestamp <= timeline.observation_end


def test_scenario_identity_preserved(sample_events, timeline):
    assert {
        event.scenario_id for event in timeline.events
    } == {
        event.scenario_id for event in sample_events
    }


def test_split_preserved(sample_events, timeline):
    assert {
        event.split for event in timeline.events
    } == {
        event.split for event in sample_events
    }


def test_event_types_preserved(sample_events, timeline):
    assert [
        event.event_type for event in timeline.events
    ] == [
        event.event_type for event in sample_events
    ]


def test_event_attributes_preserved(sample_events, timeline):
    assert [
        event.attributes for event in timeline.events
    ] == [
        event.attributes for event in sample_events
    ]


def test_original_events_not_modified(sample_events):
    original_times = [event.event_time for event in sample_events]
    align_cycle3_timeline(sample_events)
    assert [event.event_time for event in sample_events] == original_times


def test_empty_events_rejected():
    with pytest.raises(ValueError, match="requires events"):
        align_cycle3_timeline([])


def test_duplicate_indexes_rejected(sample_events):
    duplicate = replace(
        sample_events[1],
        sequence_index=sample_events[0].sequence_index,
    )
    with pytest.raises(ValueError, match="Duplicate"):
        align_cycle3_timeline([sample_events[0], duplicate])


def test_noncontiguous_indexes_rejected(sample_events):
    altered = [
        replace(event, sequence_index=event.sequence_index + 1)
        for event in sample_events
    ]
    with pytest.raises(ValueError, match="contiguous"):
        align_cycle3_timeline(altered)


def test_mixed_scenarios_rejected(sample_events):
    altered = replace(
        sample_events[1],
        scenario_id="different-scenario",
    )
    with pytest.raises(ValueError, match="mix scenarios"):
        align_cycle3_timeline([sample_events[0], altered])


def test_mixed_splits_rejected(sample_events):
    other_split = (
        "calibration"
        if sample_events[0].split == "development"
        else "development"
    )
    altered = replace(sample_events[1], split=other_split)
    with pytest.raises(ValueError, match="mix splits"):
        align_cycle3_timeline([sample_events[0], altered])


def test_holdout_split_rejected(sample_events):
    altered = replace(sample_events[0], split="holdout")
    with pytest.raises(ValueError, match="Unsupported"):
        align_cycle3_timeline([altered])


def test_naive_timestamp_rejected(sample_events):
    altered = replace(
        sample_events[0],
        event_time="2026-01-01T06:00:00",
    )
    with pytest.raises(ValueError, match="Naive"):
        align_cycle3_timeline([altered])


def test_invalid_timestamp_rejected(sample_events):
    altered = replace(
        sample_events[0],
        event_time="not-a-timestamp",
    )
    with pytest.raises(ValueError):
        align_cycle3_timeline([altered])


def test_horizon_overflow_rejected(sample_events):
    events = [
        replace(
            sample_events[0],
            sequence_index=index,
        )
        for index in range(OBSERVATION_HORIZON_MINUTES + 2)
    ]
    with pytest.raises(ValueError, match="exceed"):
        align_cycle3_timeline(events)


def test_timeline_dataclass_immutable(timeline):
    with pytest.raises(FrozenInstanceError):
        timeline.start_time = datetime.now(timezone.utc)


def test_events_container_immutable(timeline):
    assert isinstance(timeline.events, tuple)


def test_alignment_deterministic(sample_events):
    assert align_cycle3_timeline(sample_events) == align_cycle3_timeline(
        sample_events
    )


def test_reversed_original_timestamps_rejected(sample_events):
    """Chronologically reversed input must not be silently corrected."""
    altered = list(sample_events)

    altered[1] = replace(
        altered[1],
        event_time=(
            datetime.fromisoformat(
                altered[0].event_time.replace("Z", "+00:00")
            ) - timedelta(seconds=30)
        ).isoformat().replace("+00:00", "Z"),
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        align_cycle3_timeline(altered)


def test_duplicate_original_timestamps_rejected(sample_events):
    """Different events cannot share an original timestamp."""
    altered = list(sample_events)

    altered[1] = replace(
        altered[1],
        event_time=altered[0].event_time,
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        align_cycle3_timeline(altered)


def test_irregular_original_intervals_accepted(sample_events):
    """Valid irregular timing is accepted, even though alignment is fixed."""
    altered = []

    for event in sample_events:
        timestamp = TIMELINE_START + timedelta(
            seconds=event.sequence_index * 75
        )

        altered.append(
            replace(
                event,
                event_time=timestamp.isoformat().replace(
                    "+00:00", "Z"
                ),
            )
        )

    timeline = align_cycle3_timeline(altered)

    assert len(timeline.events) == len(altered)

    for event in timeline.events:
        expected = TIMELINE_START + timedelta(
            seconds=event.sequence_index * 75
        )

        actual = datetime.fromisoformat(
            event.event_time.replace("Z", "+00:00")
        )

        assert actual == expected



def test_original_timeline_beyond_horizon_rejected(sample_events):
    """Events extending beyond the shared horizon must be rejected."""
    altered = []

    for event in sample_events:
        timestamp = TIMELINE_START + timedelta(
            minutes=event.sequence_index * 3
        )

        altered.append(
            replace(
                event,
                event_time=timestamp.isoformat().replace(
                    "+00:00", "Z"
                ),
            )
        )

    with pytest.raises(ValueError, match="exceeds observation horizon"):
        align_cycle3_timeline(altered)
