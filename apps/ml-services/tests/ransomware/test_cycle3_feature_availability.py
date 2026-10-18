"""Tests for Cycle 3 feature-specific measurement availability."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from config.ransomware.scenarios.cycle3_feature_availability import (
    Cycle3FeatureAvailability,
    audit_cycle3_feature_availability,
)


COMPATIBLE = {
    "privilege_change_activity": ("privilege_change", False),
    "file_write_activity": ("write_count", 0),
    "file_rename_activity": ("rename_count", 0),
    "service_state_observation": ("service_available", False),
    "telemetry_freshness_observation": ("ingestion_lag_seconds", 0.0),
}


def event(event_type, attributes):
    return SimpleNamespace(
        event_type=event_type,
        attributes=attributes,
    )


def by_type(events):
    return {
        result.event_type: result
        for result in audit_cycle3_feature_availability(events)
    }


def test_empty_window_marks_all_five_missing():
    results = audit_cycle3_feature_availability([])

    assert len(results) == 5
    assert all(result.status == "missing" for result in results)
    assert all(result.observed_count == 0 for result in results)
    assert all(result.valid_count == 0 for result in results)
    assert all(result.invalid_count == 0 for result in results)


@pytest.mark.parametrize(
    "event_type,attribute,value",
    [
        (event_type, attribute, value)
        for event_type, (attribute, value) in COMPATIBLE.items()
    ],
)
def test_explicit_zero_or_false_is_available(
    event_type, attribute, value
):
    results = by_type([
        event(event_type, {attribute: value})
    ])

    result = results[event_type]

    assert result.status == "available"
    assert result.observed_count == 1
    assert result.valid_count == 1
    assert result.invalid_count == 0


@pytest.mark.parametrize(
    "event_type,attribute",
    [
        (event_type, attribute)
        for event_type, (attribute, _) in COMPATIBLE.items()
    ],
)
def test_missing_attribute_is_invalid(event_type, attribute):
    results = by_type([
        event(event_type, {})
    ])

    result = results[event_type]

    assert result.status == "invalid"
    assert result.observed_count == 1
    assert result.valid_count == 0
    assert result.invalid_count == 1


@pytest.mark.parametrize(
    "event_type,attribute",
    [
        (event_type, attribute)
        for event_type, (attribute, _) in COMPATIBLE.items()
    ],
)
def test_none_measurement_is_invalid(event_type, attribute):
    results = by_type([
        event(event_type, {attribute: None})
    ])

    result = results[event_type]

    assert result.status == "invalid"
    assert result.invalid_count == 1


@pytest.mark.parametrize(
    "event_type,attribute,value",
    [
        ("privilege_change_activity", "privilege_change", 1),
        ("file_write_activity", "write_count", -1),
        ("file_rename_activity", "rename_count", 1.5),
        ("service_state_observation", "service_available", 0),
        ("telemetry_freshness_observation", "ingestion_lag_seconds", -1.0),
    ],
)
def test_invalid_measurements_are_rejected(
    event_type, attribute, value
):
    result = by_type([
        event(event_type, {attribute: value})
    ])[event_type]

    assert result.status == "invalid"
    assert result.valid_count == 0
    assert result.invalid_count == 1


def test_mixed_event_window_tracks_each_feature_separately():
    results = by_type([
        event("file_write_activity", {"write_count": 0}),
        event("service_state_observation", {"service_available": False}),
        event("unrelated_observation", {"value": 10}),
    ])

    assert results["file_write_activity"].status == "available"
    assert results["service_state_observation"].status == "available"
    assert results["file_rename_activity"].status == "missing"
    assert results["privilege_change_activity"].status == "missing"
    assert results["telemetry_freshness_observation"].status == "missing"


def test_invalid_observation_overrides_valid_observation():
    results = by_type([
        event("file_write_activity", {"write_count": 5}),
        event("file_write_activity", {"write_count": -1}),
    ])

    result = results["file_write_activity"]

    assert result.status == "invalid"
    assert result.observed_count == 2
    assert result.valid_count == 1
    assert result.invalid_count == 1


def test_unresolved_evidence_does_not_become_available():
    results = by_type([
        event(
            "maintenance_authorization_observation",
            {"maintenance_approved": True},
        )
    ])

    assert len(results) == 5
    assert all(
        result.status == "missing"
        for result in results.values()
    )


def test_audit_is_deterministic():
    events = [
        event("file_write_activity", {"write_count": 3}),
        event("service_state_observation", {"service_available": True}),
    ]

    assert audit_cycle3_feature_availability(
        events
    ) == audit_cycle3_feature_availability(events)


def test_result_is_immutable():
    result = audit_cycle3_feature_availability([])[0]

    with pytest.raises(FrozenInstanceError):
        result.status = "available"


def test_result_has_expected_type():
    result = audit_cycle3_feature_availability([])[0]

    assert isinstance(result, Cycle3FeatureAvailability)


def test_input_generator_is_supported():
    events = (
        event("file_write_activity", {"write_count": value})
        for value in [0, 2, 3]
    )

    result = by_type(events)["file_write_activity"]

    assert result.status == "available"
    assert result.observed_count == 3
    assert result.valid_count == 3


def test_no_default_measurement_is_created():
    result = by_type([
        event("file_write_activity", {})
    ])["file_write_activity"]

    assert result.status == "invalid"
    assert result.valid_count == 0


def test_feature_names_match_mapping_contract():
    results = audit_cycle3_feature_availability([])

    expected = {
        "privilege_change_count",
        "write_rate",
        "rename_rate",
        "service_availability_ratio",
        "ingestion_lag_seconds",
    }

    assert {result.feature_name for result in results} == expected
