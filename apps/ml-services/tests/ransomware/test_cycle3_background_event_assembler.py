"""Tests for the Cycle 3 validated background event assembler."""

from collections import Counter
from dataclasses import fields
from datetime import datetime, timedelta, timezone

import pytest

from config.ransomware.scenarios.cycle3_background_event_assembler import (
    BACKGROUND_START_TIME,
    assemble_cycle3_background_events,
)
from config.ransomware.scenarios.cycle3_background_measurements import (
    build_cycle3_background_measurements,
)
from config.ransomware.scenarios.cycle3_evidence_quality_gate import (
    evaluate_cycle3_evidence_quality,
)
from config.ransomware.scenarios.cycle3_measurement_profile import (
    build_cycle3_measurement_profile,
)
from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    evaluate_cycle3_measurement_value,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


BASE_INPUTS = {
    "base_seed": 20261017,
    "sector": "energy",
    "asset_id": "energy-asset-01",
    "use_case_id": "EN-RW-01",
    "scenario_id": "test-scenario-001",
    "scenario_seed": 12345,
    "split": "development",
}


def build(**overrides):
    inputs = dict(BASE_INPUTS)
    inputs.update(overrides)
    return assemble_cycle3_background_events(**inputs)


def test_returns_tuple():
    assert isinstance(build(), tuple)


def test_produces_exactly_75_events():
    assert len(build()) == 75


def test_events_are_observable_scenario_events():
    assert all(
        isinstance(event, ObservableScenarioEvent)
        for event in build()
    )


def test_assembler_is_deterministic():
    assert build() == build()


def test_sequence_indices_are_contiguous():
    assert [
        event.sequence_index
        for event in build()
    ] == list(range(75))


def test_start_time_is_utc():
    assert BACKGROUND_START_TIME.tzinfo == timezone.utc


def test_five_events_share_each_minute():
    counts = Counter(
        event.event_time
        for event in build()
    )

    assert len(counts) == 15
    assert set(counts.values()) == {5}


def test_event_timestamps_match_measurement_schedule():
    events = build()
    measurements = build_cycle3_background_measurements(
        base_seed=BASE_INPUTS["base_seed"],
        sector=BASE_INPUTS["sector"],
        asset_id=BASE_INPUTS["asset_id"],
        use_case_id=BASE_INPUTS["use_case_id"],
    )

    for event, measurement in zip(events, measurements):
        expected_time = (
            BACKGROUND_START_TIME
            + timedelta(minutes=measurement.observation_minute)
        )

        actual_time = datetime.fromisoformat(
            event.event_time.replace("Z", "+00:00")
        )

        assert actual_time == expected_time
        assert actual_time.utcoffset() == timedelta(0)


def test_event_types_match_measurement_schedule():
    measurements = build_cycle3_background_measurements(
        base_seed=BASE_INPUTS["base_seed"],
        sector=BASE_INPUTS["sector"],
        asset_id=BASE_INPUTS["asset_id"],
        use_case_id=BASE_INPUTS["use_case_id"],
    )

    assert tuple(
        event.event_type for event in build()
    ) == tuple(
        measurement.event_type for measurement in measurements
    )


def test_event_attributes_preserve_validated_measurements():
    measurements = build_cycle3_background_measurements(
        base_seed=BASE_INPUTS["base_seed"],
        sector=BASE_INPUTS["sector"],
        asset_id=BASE_INPUTS["asset_id"],
        use_case_id=BASE_INPUTS["use_case_id"],
    )

    expected_attributes = {
        "privilege_change_activity": "privilege_change",
        "file_write_activity": "write_count",
        "file_rename_activity": "rename_count",
        "service_state_observation": "service_available",
        "telemetry_freshness_observation": "ingestion_lag_seconds",
    }

    for event, measurement in zip(build(), measurements):
        attribute_name = expected_attributes[event.event_type]

        assert event.attributes == {
            attribute_name: measurement.measured_value
        }

        decision = evaluate_cycle3_measurement_value(
            event.event_type,
            event.attributes[attribute_name],
        )

        assert decision.allowed


def test_all_five_evidence_types_are_present():
    profile = build_cycle3_measurement_profile()

    assert set(
        event.event_type for event in build()
    ) == set(profile.event_types)


def test_evidence_quality_gate_passes_for_complete_schedule():
    profile = build_cycle3_measurement_profile()

    decision = evaluate_cycle3_evidence_quality(
        build(),
        required_event_types=profile.event_types,
    )

    assert decision.passed
    assert decision.reasons == ()
    assert decision.quarantined == ()


@pytest.mark.parametrize(
    "field",
    ("scenario_id", "scenario_seed", "split"),
)
def test_provenance_changes_do_not_change_measurements(field):
    replacements = {
        "scenario_id": "test-scenario-002",
        "scenario_seed": 67890,
        "split": "calibration",
    }

    first = build()
    second = build(**{field: replacements[field]})

    def measurement_signature(events):
        return tuple(
            (
                event.sequence_index,
                event.event_time,
                event.event_type,
                tuple(sorted(event.attributes.items())),
            )
            for event in events
        )

    assert measurement_signature(first) == measurement_signature(second)


def test_provenance_is_preserved():
    for event in build():
        assert event.scenario_id == BASE_INPUTS["scenario_id"]
        assert event.scenario_seed == BASE_INPUTS["scenario_seed"]
        assert event.split == BASE_INPUTS["split"]
        assert event.asset_id == BASE_INPUTS["asset_id"]


def test_model_facing_attributes_exclude_provenance_and_labels():
    forbidden = {
        "variant",
        "split",
        "scenario_id",
        "scenario_seed",
        "scenario_family",
        "label",
        "attack_label",
        "stage",
        "lifecycle_stage",
        "is_attack",
    }

    for event in build():
        assert set(event.attributes).isdisjoint(forbidden)


def test_event_dataclass_has_expected_provenance_fields():
    names = {
        item.name for item in fields(ObservableScenarioEvent)
    }

    assert {
        "scenario_id",
        "scenario_seed",
        "split",
        "sequence_index",
        "event_time",
        "event_type",
        "asset_id",
        "attributes",
    }.issubset(names)


@pytest.mark.parametrize(
    "invalid_split",
    ("holdout", "test", "", None),
)
def test_invalid_split_is_rejected(invalid_split):
    with pytest.raises(ValueError):
        build(split=invalid_split)


@pytest.mark.parametrize(
    "invalid_id",
    ("", "   ", None, 123),
)
def test_invalid_scenario_id_is_rejected(invalid_id):
    with pytest.raises(ValueError):
        build(scenario_id=invalid_id)


@pytest.mark.parametrize(
    "invalid_seed",
    (-1, True, 1.5, None),
)
def test_invalid_scenario_seed_is_rejected(invalid_seed):
    with pytest.raises(ValueError):
        build(scenario_seed=invalid_seed)


def test_original_input_dictionary_is_unchanged():
    inputs = dict(BASE_INPUTS)

    assemble_cycle3_background_events(**inputs)

    assert inputs == BASE_INPUTS
