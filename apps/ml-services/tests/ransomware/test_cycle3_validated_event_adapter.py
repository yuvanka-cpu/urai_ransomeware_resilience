"""Tests for Cycle 3 validated observable-event construction."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)
from config.ransomware.scenarios.cycle3_validated_event_adapter import (
    build_cycle3_validated_event,
)


BASE_TIME = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)

BASE_ARGS = {
    "scenario_id": "cycle3-development-example",
    "scenario_seed": 12345,
    "split": "development",
    "sequence_index": 0,
    "event_time": BASE_TIME,
    "asset_id": "energy-example-asset",
    "event_type": "file_write_activity",
    "measured_value": 5,
}


def build_event(**overrides):
    arguments = {**BASE_ARGS, **overrides}
    return build_cycle3_validated_event(**arguments)


def test_returns_existing_event_dataclass():
    assert isinstance(build_event(), ObservableScenarioEvent)


def test_preserves_scenario_identity():
    event = build_event()
    assert event.scenario_id == BASE_ARGS["scenario_id"]
    assert event.scenario_seed == BASE_ARGS["scenario_seed"]


def test_preserves_asset_identity():
    assert build_event().asset_id == BASE_ARGS["asset_id"]


def test_preserves_split():
    assert build_event().split == "development"


def test_accepts_calibration_split():
    assert build_event(split="calibration").split == "calibration"


def test_preserves_sequence_index():
    assert build_event(sequence_index=7).sequence_index == 7


def test_utc_timestamp_format():
    assert build_event().event_time == "2026-01-01T06:00:00Z"


def test_converts_offset_timestamp_to_utc():
    local_time = datetime(
        2026, 1, 1, 11, 30,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )
    assert build_event(event_time=local_time).event_time == (
        "2026-01-01T06:00:00Z"
    )


def test_event_type_preserved():
    assert build_event().event_type == "file_write_activity"


def test_event_family_comes_from_vocabulary():
    assert build_event().event_family == "file"


def test_validated_count_attribute():
    assert build_event().attributes == {"write_count": 5}


def test_zero_count_is_preserved():
    assert build_event(measured_value=0).attributes == {
        "write_count": 0
    }


def test_valid_boolean_attribute():
    event = build_event(
        event_type="service_state_observation",
        measured_value=False,
    )
    assert event.attributes == {"service_available": False}


def test_valid_privilege_change_boolean():
    event = build_event(
        event_type="privilege_change_activity",
        measured_value=True,
    )
    assert event.attributes == {"privilege_change": True}


def test_valid_duration_attribute():
    event = build_event(
        event_type="telemetry_freshness_observation",
        measured_value=2.5,
    )
    assert event.attributes == {"ingestion_lag_seconds": 2.5}


@pytest.mark.parametrize("value", [True, False])
def test_maintenance_authorization_is_quarantined(value):
    with pytest.raises(
        ValueError,
        match="unresolved_measurement_semantics",
    ):
        build_event(
            event_type="maintenance_authorization_observation",
            measured_value=value,
        )


@pytest.mark.parametrize(
    "scenario_id",
    ["", "   ", None, 123],
)
def test_invalid_scenario_identity_rejected(scenario_id):
    with pytest.raises(ValueError, match="Invalid scenario_id"):
        build_event(scenario_id=scenario_id)


@pytest.mark.parametrize(
    "seed",
    [-1, 1.5, True, None],
)
def test_invalid_seed_rejected(seed):
    with pytest.raises(ValueError, match="Invalid scenario_seed"):
        build_event(scenario_seed=seed)


@pytest.mark.parametrize(
    "split",
    ["holdout", "test", "training", "", None],
)
def test_invalid_split_rejected(split):
    with pytest.raises(ValueError, match="Invalid Cycle 3 split"):
        build_event(split=split)


@pytest.mark.parametrize(
    "index",
    [-1, 1.5, True, None],
)
def test_invalid_sequence_index_rejected(index):
    with pytest.raises(ValueError, match="Invalid sequence_index"):
        build_event(sequence_index=index)


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        "2026-01-01T06:00:00Z",
        123,
    ],
)
def test_invalid_timestamp_type_rejected(timestamp):
    with pytest.raises(ValueError, match="Invalid event_time"):
        build_event(event_time=timestamp)


def test_naive_timestamp_rejected():
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        build_event(
            event_time=datetime(2026, 1, 1, 6, 0)
        )


@pytest.mark.parametrize(
    "asset_id",
    ["", "   ", None, 123],
)
def test_invalid_asset_identity_rejected(asset_id):
    with pytest.raises(ValueError, match="Invalid asset_id"):
        build_event(asset_id=asset_id)


@pytest.mark.parametrize(
    "event_type",
    [
        "authentication_activity",
        "remote_session_activity",
        "network_peer_activity",
        "backup_status_observation",
        "restore_test_observation",
        "communications_state_observation",
    ],
)
def test_unresolved_evidence_rejected(event_type):
    with pytest.raises(
        ValueError,
        match="unresolved_measurement_semantics",
    ):
        build_event(event_type=event_type)


@pytest.mark.parametrize(
    "event_type",
    [
        "unknown_observation",
        "initial_access_observable",
        "attack_activity",
    ],
)
def test_unknown_evidence_rejected(event_type):
    with pytest.raises(
        ValueError,
        match="unknown_evidence_type",
    ):
        build_event(event_type=event_type)


@pytest.mark.parametrize(
    "value",
    [-1, 1.5, True, None, "5"],
)
def test_invalid_file_counts_rejected(value):
    with pytest.raises(ValueError, match="measurement rejected"):
        build_event(measured_value=value)


@pytest.mark.parametrize(
    "value",
    [0, 1, None, "true"],
)
def test_invalid_service_booleans_rejected(value):
    with pytest.raises(ValueError, match="measurement rejected"):
        build_event(
            event_type="service_state_observation",
            measured_value=value,
        )


@pytest.mark.parametrize(
    "value",
    [-1, float("nan"), float("inf"), True],
)
def test_invalid_ingestion_lag_rejected(value):
    with pytest.raises(ValueError, match="measurement rejected"):
        build_event(
            event_type="telemetry_freshness_observation",
            measured_value=value,
        )


def test_event_has_no_variant_attribute():
    assert "variant" not in build_event().attributes


def test_event_has_no_stage_attribute():
    assert "stage" not in build_event().attributes


def test_event_has_no_label_attribute():
    assert "label" not in build_event().attributes


def test_event_has_no_generic_intensity_attribute():
    attributes = build_event().attributes

    assert "activity_intensity" not in attributes
    assert "degradation_severity" not in attributes
    assert "observable_value" not in attributes


def test_event_dataclass_is_frozen():
    event = build_event()

    with pytest.raises(FrozenInstanceError):
        event.event_type = "modified"


def test_construction_is_deterministic():
    assert build_event() == build_event()


def test_different_measurements_remain_distinct():
    first = build_event(measured_value=5)
    second = build_event(measured_value=10)

    assert first.attributes != second.attributes


def test_different_sequence_indices_remain_distinct():
    first = build_event(sequence_index=0)
    second = build_event(sequence_index=1)

    assert first.sequence_index != second.sequence_index


def test_no_operational_action_field_is_added():
    assert "operational_action_executed" not in build_event().attributes
