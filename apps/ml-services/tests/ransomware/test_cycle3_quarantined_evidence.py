"""Regression tests for Cycle 3 quarantined evidence reporting."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from config.ransomware.scenarios.cycle3_feature_availability import (
    Cycle3QuarantinedEvidence,
    audit_cycle3_feature_availability,
    audit_cycle3_quarantined_evidence,
)


def event(event_type, attributes=None):
    return SimpleNamespace(
        event_type=event_type,
        attributes={} if attributes is None else attributes,
    )


def test_empty_input_returns_empty_report():
    assert audit_cycle3_quarantined_evidence([]) == ()


def test_compatible_evidence_is_not_quarantined():
    events = [
        event("privilege_change_activity", {"privilege_change": False}),
        event("file_write_activity", {"write_count": 0}),
        event("file_rename_activity", {"rename_count": 0}),
        event("service_state_observation", {"service_available": False}),
        event(
            "telemetry_freshness_observation",
            {"ingestion_lag_seconds": 0.0},
        ),
    ]

    assert audit_cycle3_quarantined_evidence(events) == ()


@pytest.mark.parametrize(
    "event_type",
    [
        "authentication_activity",
        "remote_session_activity",
        "network_peer_activity",
        "backup_status_observation",
        "restore_test_observation",
        "communications_state_observation",
        "maintenance_authorization_observation",
    ],
)
def test_each_unresolved_type_is_reported(event_type):
    report = audit_cycle3_quarantined_evidence([
        event(event_type)
    ])

    assert len(report) == 1
    assert report[0].event_type == event_type
    assert report[0].reason == "unresolved_measurement_semantics"
    assert report[0].observed_count == 1


def test_unknown_evidence_is_reported():
    report = audit_cycle3_quarantined_evidence([
        event("unknown_cycle3_observation")
    ])

    assert len(report) == 1
    assert report[0].event_type == "unknown_cycle3_observation"
    assert report[0].reason == "unknown_evidence_type"
    assert report[0].observed_count == 1


def test_repeated_rejected_events_are_counted():
    report = audit_cycle3_quarantined_evidence([
        event("maintenance_authorization_observation"),
        event("maintenance_authorization_observation"),
        event("maintenance_authorization_observation"),
    ])

    assert len(report) == 1
    assert report[0].observed_count == 3


def test_different_rejection_reasons_are_separate():
    report = audit_cycle3_quarantined_evidence([
        event("maintenance_authorization_observation"),
        event("unknown_cycle3_observation"),
    ])

    assert len(report) == 2

    reasons = {
        item.event_type: item.reason
        for item in report
    }

    assert reasons == {
        "maintenance_authorization_observation":
            "unresolved_measurement_semantics",
        "unknown_cycle3_observation":
            "unknown_evidence_type",
    }


def test_mixed_window_reports_only_rejected_evidence():
    events = [
        event("file_write_activity", {"write_count": 5}),
        event("maintenance_authorization_observation"),
        event("unknown_cycle3_observation"),
        event("service_state_observation", {"service_available": True}),
    ]

    report = audit_cycle3_quarantined_evidence(events)

    assert len(report) == 2
    assert {
        item.event_type for item in report
    } == {
        "maintenance_authorization_observation",
        "unknown_cycle3_observation",
    }


def test_report_is_deterministic_across_input_order():
    events = [
        event("unknown_cycle3_observation"),
        event("maintenance_authorization_observation"),
        event("authentication_activity"),
    ]

    assert audit_cycle3_quarantined_evidence(
        events
    ) == audit_cycle3_quarantined_evidence(
        reversed(events)
    )


def test_report_is_sorted_by_event_type():
    report = audit_cycle3_quarantined_evidence([
        event("unknown_cycle3_observation"),
        event("maintenance_authorization_observation"),
        event("authentication_activity"),
    ])

    names = [item.event_type for item in report]

    assert names == sorted(names)


def test_generator_input_is_supported():
    events = (
        event("maintenance_authorization_observation")
        for _ in range(4)
    )

    report = audit_cycle3_quarantined_evidence(events)

    assert len(report) == 1
    assert report[0].observed_count == 4


def test_report_result_is_immutable():
    result = audit_cycle3_quarantined_evidence([
        event("maintenance_authorization_observation")
    ])[0]

    assert isinstance(result, Cycle3QuarantinedEvidence)

    with pytest.raises(FrozenInstanceError):
        result.observed_count = 99


def test_existing_feature_availability_contract_is_preserved():
    events = [
        event("file_write_activity", {"write_count": 0}),
        event("maintenance_authorization_observation"),
    ]

    availability = audit_cycle3_feature_availability(events)
    quarantine = audit_cycle3_quarantined_evidence(events)

    assert len(availability) == 5
    assert len(quarantine) == 1

    write_result = next(
        item
        for item in availability
        if item.event_type == "file_write_activity"
    )

    assert write_result.status == "available"
    assert quarantine[0].event_type == (
        "maintenance_authorization_observation"
    )


def test_no_feature_values_are_created():
    report = audit_cycle3_quarantined_evidence([
        event("maintenance_authorization_observation")
    ])

    assert len(report) == 1
    assert not hasattr(report[0], "feature_name")
    assert not hasattr(report[0], "feature_value")
