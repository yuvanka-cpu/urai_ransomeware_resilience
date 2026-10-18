"""Tests for the Cycle 3 fail-closed evidence mapping gate."""

from dataclasses import FrozenInstanceError

import pytest

from config.ransomware.scenarios.cycle3_evidence_feature_contract import (
    EVIDENCE_FEATURE_MAPPINGS,
)

from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    Cycle3EvidenceMappingDecision,
    evaluate_cycle3_evidence_mapping,
    require_cycle3_evidence_mapping,
)


COMPATIBLE_TYPES = (
    "privilege_change_activity",
    "file_write_activity",
    "file_rename_activity",
    "service_state_observation",
    "telemetry_freshness_observation",
)

UNRESOLVED_TYPES = (
    "maintenance_authorization_observation",
    "authentication_activity",
    "remote_session_activity",
    "network_peer_activity",
    "backup_status_observation",
    "restore_test_observation",
    "communications_state_observation",
)


@pytest.mark.parametrize("event_type", COMPATIBLE_TYPES)
def test_compatible_evidence_is_allowed(event_type):
    decision = evaluate_cycle3_evidence_mapping(event_type)

    assert decision.allowed is True
    assert decision.event_type == event_type
    assert decision.mapping is not None
    assert decision.reason is None


@pytest.mark.parametrize("event_type", COMPATIBLE_TYPES)
def test_compatible_evidence_has_complete_mapping(event_type):
    decision = evaluate_cycle3_evidence_mapping(event_type)

    assert decision.mapping is not None
    assert decision.mapping.attribute_name
    assert decision.mapping.feature_name


@pytest.mark.parametrize("event_type", COMPATIBLE_TYPES)
def test_require_returns_compatible_mapping(event_type):
    mapping = require_cycle3_evidence_mapping(event_type)

    assert mapping.event_type == event_type
    assert mapping.status == "compatible_with_constraints"


@pytest.mark.parametrize("event_type", UNRESOLVED_TYPES)
def test_unresolved_evidence_is_rejected(event_type):
    decision = evaluate_cycle3_evidence_mapping(event_type)

    assert decision.allowed is False
    assert decision.mapping is None
    assert decision.reason == "unresolved_measurement_semantics"


@pytest.mark.parametrize("event_type", UNRESOLVED_TYPES)
def test_require_rejects_unresolved_evidence(event_type):
    with pytest.raises(
        ValueError,
        match="unresolved_measurement_semantics",
    ):
        require_cycle3_evidence_mapping(event_type)


@pytest.mark.parametrize(
    "event_type",
    (
        "unknown_observation",
        "initial_access_observable",
        "attack_activity",
        "",
    ),
)
def test_unknown_evidence_is_rejected(event_type):
    decision = evaluate_cycle3_evidence_mapping(event_type)

    assert decision.allowed is False
    assert decision.mapping is None
    assert decision.reason == "unknown_evidence_type"


@pytest.mark.parametrize(
    "event_type",
    (
        "unknown_observation",
        "initial_access_observable",
        "attack_activity",
        "",
    ),
)
def test_require_rejects_unknown_evidence(event_type):
    with pytest.raises(
        ValueError,
        match="unknown_evidence_type",
    ):
        require_cycle3_evidence_mapping(event_type)


def test_decision_is_frozen():
    decision = evaluate_cycle3_evidence_mapping(
        "file_write_activity"
    )

    with pytest.raises(FrozenInstanceError):
        decision.allowed = False


def test_decision_has_expected_type():
    decision = evaluate_cycle3_evidence_mapping(
        "file_write_activity"
    )

    assert isinstance(decision, Cycle3EvidenceMappingDecision)


def test_lookup_is_deterministic():
    first = evaluate_cycle3_evidence_mapping(
        "file_write_activity"
    )

    second = evaluate_cycle3_evidence_mapping(
        "file_write_activity"
    )

    assert first == second


def test_allowed_mapping_matches_contract():
    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        decision = evaluate_cycle3_evidence_mapping(
            mapping.event_type
        )

        if mapping.status == "compatible_with_constraints":
            assert decision.allowed is True
            assert decision.mapping == mapping
        else:
            assert decision.allowed is False
            assert decision.mapping is None


def test_all_five_compatible_types_are_allowed():
    allowed = [
        event_type
        for event_type in COMPATIBLE_TYPES
        if evaluate_cycle3_evidence_mapping(event_type).allowed
    ]

    assert len(allowed) == 5


def test_all_seven_unresolved_types_are_rejected():
    rejected = [
        event_type
        for event_type in UNRESOLVED_TYPES
        if not evaluate_cycle3_evidence_mapping(event_type).allowed
    ]

    assert len(rejected) == 7


def test_no_rejected_decision_exposes_mapping():
    for event_type in UNRESOLVED_TYPES + (
        "unknown_observation",
    ):
        decision = evaluate_cycle3_evidence_mapping(event_type)

        assert decision.allowed is False
        assert decision.mapping is None


def test_rejection_includes_event_type():
    with pytest.raises(ValueError) as exc:
        require_cycle3_evidence_mapping(
            "backup_status_observation"
        )

    assert "backup_status_observation" in str(exc.value)


def test_rejection_does_not_return_default_mapping():
    decision = evaluate_cycle3_evidence_mapping(
        "unknown_observation"
    )

    assert decision.mapping is None
    assert decision.allowed is False


def test_file_write_mapping_is_preserved():
    mapping = require_cycle3_evidence_mapping(
        "file_write_activity"
    )

    assert mapping.attribute_name == "write_count"
    assert mapping.feature_name == "write_rate"


def test_telemetry_lag_mapping_is_preserved():
    mapping = require_cycle3_evidence_mapping(
        "telemetry_freshness_observation"
    )

    assert mapping.attribute_name == "ingestion_lag_seconds"
    assert mapping.feature_name == "ingestion_lag_seconds"
