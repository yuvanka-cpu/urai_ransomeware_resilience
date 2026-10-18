"""Tests for Cycle 3 fail-closed measurement-value validation."""

from dataclasses import FrozenInstanceError

import pytest

from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    Cycle3MeasurementValueDecision,
    evaluate_cycle3_measurement_value,
    require_cycle3_measurement_value,
)


@pytest.mark.parametrize(
    "event_type,value",
    [
        ("file_write_activity", 0),
        ("file_write_activity", 1),
        ("file_write_activity", 100),
        ("file_rename_activity", 0),
        ("file_rename_activity", 25),
    ],
)
def test_valid_counts_are_accepted(event_type, value):
    decision = evaluate_cycle3_measurement_value(event_type, value)
    assert decision.allowed is True
    assert decision.value == value
    assert decision.reason is None


@pytest.mark.parametrize(
    "value",
    [-1, -100, 1.5, 0.0, True, False, "5", None],
)
def test_invalid_counts_are_rejected(value):
    decision = evaluate_cycle3_measurement_value(
        "file_write_activity", value
    )
    assert decision.allowed is False
    assert decision.value is None


@pytest.mark.parametrize(
    "event_type",
    [
        "privilege_change_activity",
        "service_state_observation",
    ],
)
@pytest.mark.parametrize("value", [True, False])
def test_valid_booleans_are_accepted(event_type, value):
    decision = evaluate_cycle3_measurement_value(event_type, value)
    assert decision.allowed is True
    assert decision.value is value


@pytest.mark.parametrize(
    "value",
    [0, 1, 0.0, 1.0, "true", "false", None, [], {}],
)
def test_invalid_booleans_are_rejected(value):
    decision = evaluate_cycle3_measurement_value(
        "service_state_observation", value
    )
    assert decision.allowed is False
    assert decision.value is None


@pytest.mark.parametrize(
    "value",
    [0, 1, 1.5, 60, 120.75],
)
def test_valid_durations_are_accepted(value):
    decision = evaluate_cycle3_measurement_value(
        "telemetry_freshness_observation", value
    )
    assert decision.allowed is True
    assert decision.value == value


@pytest.mark.parametrize(
    "value,expected_reason",
    [
        (-1, "negative_duration"),
        (-0.5, "negative_duration"),
        (float("nan"), "nonfinite_duration"),
        (float("inf"), "nonfinite_duration"),
        (float("-inf"), "nonfinite_duration"),
        (True, "invalid_duration"),
        ("60", "invalid_duration"),
        ([], "invalid_duration"),
    ],
)
def test_invalid_durations_are_rejected(value, expected_reason):
    decision = evaluate_cycle3_measurement_value(
        "telemetry_freshness_observation", value
    )
    assert decision.allowed is False
    assert decision.reason == expected_reason
    assert decision.value is None


@pytest.mark.parametrize(
    "event_type",
    [
        "file_write_activity",
        "file_rename_activity",
        "service_state_observation",
        "telemetry_freshness_observation",
    ],
)
def test_missing_measurements_are_rejected(event_type):
    decision = evaluate_cycle3_measurement_value(event_type, None)
    assert decision.allowed is False
    assert decision.reason == "missing_measurement"


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
def test_unresolved_evidence_is_rejected(event_type):
    decision = evaluate_cycle3_measurement_value(event_type, 1)
    assert decision.allowed is False
    assert decision.reason == "unresolved_measurement_semantics"
    assert decision.value is None


@pytest.mark.parametrize(
    "event_type",
    ["unknown_event", "attack_activity", ""],
)
def test_unknown_evidence_is_rejected(event_type):
    decision = evaluate_cycle3_measurement_value(event_type, 1)
    assert decision.allowed is False
    assert decision.reason == "unknown_evidence_type"


@pytest.mark.parametrize(
    "event_type,value",
    [
        ("file_write_activity", 5),
        ("file_rename_activity", 2),
        ("service_state_observation", True),
        ("privilege_change_activity", False),
        ("telemetry_freshness_observation", 2.5),
    ],
)
def test_require_returns_valid_measurements(event_type, value):
    result = require_cycle3_measurement_value(event_type, value)
    assert result == value
    assert type(result) is type(value)


@pytest.mark.parametrize(
    "event_type,value",
    [
        ("file_write_activity", -1),
        ("file_rename_activity", 1.5),
        ("service_state_observation", 1),
        ("telemetry_freshness_observation", float("nan")),
        ("authentication_activity", 3),
        ("unknown_event", 5),
    ],
)
def test_require_rejects_invalid_measurements(event_type, value):
    with pytest.raises(ValueError, match="Cycle 3 measurement rejected"):
        require_cycle3_measurement_value(event_type, value)


def test_decision_is_immutable():
    decision = evaluate_cycle3_measurement_value(
        "file_write_activity", 5
    )
    with pytest.raises(FrozenInstanceError):
        decision.allowed = False


def test_decision_has_expected_type():
    decision = evaluate_cycle3_measurement_value(
        "file_write_activity", 5
    )
    assert isinstance(decision, Cycle3MeasurementValueDecision)


def test_validation_is_deterministic():
    first = evaluate_cycle3_measurement_value(
        "file_write_activity", 5
    )
    second = evaluate_cycle3_measurement_value(
        "file_write_activity", 5
    )
    assert first == second


def test_missing_count_is_not_substituted_with_zero():
    decision = evaluate_cycle3_measurement_value(
        "file_write_activity", None
    )
    assert decision.allowed is False
    assert decision.value is None


def test_zero_count_is_distinct_from_missing():
    zero = evaluate_cycle3_measurement_value(
        "file_write_activity", 0
    )
    missing = evaluate_cycle3_measurement_value(
        "file_write_activity", None
    )
    assert zero.allowed is True
    assert missing.allowed is False


def test_false_boolean_is_distinct_from_missing():
    observed_false = evaluate_cycle3_measurement_value(
        "service_state_observation", False
    )
    missing = evaluate_cycle3_measurement_value(
        "service_state_observation", None
    )
    assert observed_false.allowed is True
    assert missing.allowed is False


def test_negative_zero_duration_is_accepted():
    decision = evaluate_cycle3_measurement_value(
        "telemetry_freshness_observation", -0.0
    )
    assert decision.allowed is True


def test_rejection_preserves_event_identity():
    decision = evaluate_cycle3_measurement_value(
        "file_write_activity", -5
    )
    assert decision.event_type == "file_write_activity"
    assert decision.reason == "invalid_count"


@pytest.mark.parametrize("value", [True, False])
def test_maintenance_authorization_is_quarantined(value):
    decision = evaluate_cycle3_measurement_value(
        "maintenance_authorization_observation",
        value,
    )

    assert decision.allowed is False
    assert decision.value is None
    assert decision.reason == "unresolved_measurement_semantics"

    with pytest.raises(
        ValueError,
        match="unresolved_measurement_semantics",
    ):
        require_cycle3_measurement_value(
            "maintenance_authorization_observation",
            value,
        )
