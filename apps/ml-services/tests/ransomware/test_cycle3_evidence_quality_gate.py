"""Regression tests for Cycle 3 evidence-quality admission."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from config.ransomware.scenarios.cycle3_evidence_quality_gate import (
    Cycle3EvidenceQualityDecision,
    evaluate_cycle3_evidence_quality,
)


def event(event_type, attributes=None):
    return SimpleNamespace(
        event_type=event_type,
        attributes={} if attributes is None else attributes,
    )


def evaluate(events, required=("file_write_activity",)):
    return evaluate_cycle3_evidence_quality(
        events,
        required_event_types=required,
    )


def test_valid_required_measurement_passes():
    decision = evaluate([
        event("file_write_activity", {"write_count": 5})
    ])

    assert decision.passed
    assert decision.reasons == ()
    assert decision.quarantined == ()


def test_explicit_zero_is_valid():
    decision = evaluate([
        event("file_write_activity", {"write_count": 0})
    ])

    assert decision.passed


def test_explicit_false_is_valid():
    decision = evaluate(
        [
            event(
                "service_state_observation",
                {"service_available": False},
            )
        ],
        required=("service_state_observation",),
    )

    assert decision.passed


def test_missing_required_measurement_fails():
    decision = evaluate([
        event("service_state_observation", {"service_available": True})
    ])

    assert not decision.passed
    assert (
        "required_evidence_missing:file_write_activity"
        in decision.reasons
    )


def test_invalid_required_measurement_fails():
    decision = evaluate([
        event("file_write_activity", {"write_count": -1})
    ])

    assert not decision.passed
    assert (
        "required_evidence_invalid:file_write_activity"
        in decision.reasons
    )


def test_valid_and_invalid_measurement_fails():
    decision = evaluate([
        event("file_write_activity", {"write_count": 3}),
        event("file_write_activity", {"write_count": -1}),
    ])

    assert not decision.passed
    assert (
        "required_evidence_invalid:file_write_activity"
        in decision.reasons
    )


def test_missing_attribute_fails():
    decision = evaluate([
        event("file_write_activity", {})
    ])

    assert not decision.passed
    assert (
        "required_evidence_invalid:file_write_activity"
        in decision.reasons
    )


def test_unknown_required_type_fails():
    decision = evaluate(
        [event("file_write_activity", {"write_count": 2})],
        required=("unknown_required_observation",),
    )

    assert not decision.passed
    assert any(
        reason.startswith(
            "invalid_required_evidence:unknown_required_observation:"
        )
        for reason in decision.reasons
    )


def test_unresolved_required_type_fails():
    decision = evaluate(
        [event("file_write_activity", {"write_count": 2})],
        required=("maintenance_authorization_observation",),
    )

    assert not decision.passed
    assert any(
        reason.startswith(
            "invalid_required_evidence:maintenance_authorization_observation:"
        )
        for reason in decision.reasons
    )


def test_quarantined_event_fails_even_with_valid_required_evidence():
    decision = evaluate([
        event("file_write_activity", {"write_count": 2}),
        event("maintenance_authorization_observation"),
    ])

    assert not decision.passed
    assert any(
        reason.startswith(
            "quarantined_evidence:maintenance_authorization_observation:"
        )
        for reason in decision.reasons
    )


def test_unknown_observation_fails():
    decision = evaluate([
        event("file_write_activity", {"write_count": 2}),
        event("unknown_cycle3_observation"),
    ])

    assert not decision.passed
    assert any(
        reason.startswith(
            "quarantined_evidence:unknown_cycle3_observation:"
        )
        for reason in decision.reasons
    )


def test_empty_window_fails():
    decision = evaluate([])

    assert not decision.passed
    assert "empty_event_window" in decision.reasons
    assert (
        "required_evidence_missing:file_write_activity"
        in decision.reasons
    )


def test_optional_missing_evidence_does_not_fail():
    decision = evaluate([
        event("file_write_activity", {"write_count": 1})
    ])

    assert decision.passed
    assert any(
        item.status == "missing"
        for item in decision.availability
        if item.event_type == "service_state_observation"
    )


def test_multiple_required_types_pass():
    decision = evaluate(
        [
            event("file_write_activity", {"write_count": 1}),
            event("service_state_observation", {"service_available": True}),
        ],
        required=(
            "file_write_activity",
            "service_state_observation",
        ),
    )

    assert decision.passed


def test_one_missing_among_multiple_required_fails():
    decision = evaluate(
        [event("file_write_activity", {"write_count": 1})],
        required=(
            "file_write_activity",
            "service_state_observation",
        ),
    )

    assert not decision.passed
    assert (
        "required_evidence_missing:service_state_observation"
        in decision.reasons
    )


@pytest.mark.parametrize(
    "required",
    [
        (),
        ("file_write_activity", "file_write_activity"),
        ("",),
        (None,),
        (123,),
    ],
)
def test_invalid_requirement_configuration_raises(required):
    with pytest.raises(ValueError):
        evaluate([], required=required)


def test_generator_events_supported():
    events = (
        event("file_write_activity", {"write_count": value})
        for value in [0, 1, 2]
    )

    assert evaluate(events).passed


def test_generator_requirements_supported():
    required = (
        value
        for value in ["file_write_activity"]
    )

    decision = evaluate(
        [event("file_write_activity", {"write_count": 1})],
        required=required,
    )

    assert decision.passed


def test_decision_is_deterministic():
    events = [
        event("file_write_activity", {"write_count": 2}),
        event("maintenance_authorization_observation"),
    ]

    assert evaluate(events) == evaluate(events)


def test_decision_is_immutable():
    decision = evaluate([
        event("file_write_activity", {"write_count": 1})
    ])

    assert isinstance(decision, Cycle3EvidenceQualityDecision)

    with pytest.raises(FrozenInstanceError):
        decision.passed = False


def test_required_types_are_preserved():
    required = (
        "service_state_observation",
        "file_write_activity",
    )

    decision = evaluate(
        [
            event("file_write_activity", {"write_count": 1}),
            event("service_state_observation", {"service_available": True}),
        ],
        required=required,
    )

    assert decision.required_event_types == required


def test_no_model_decision_fields_are_created():
    decision = evaluate([
        event("file_write_activity", {"write_count": 1})
    ])

    assert not hasattr(decision, "risk_score")
    assert not hasattr(decision, "model_prediction")
    assert not hasattr(decision, "real_action_executed")
