import pytest

from config.ransomware.shared.dlq_contract import (
    DLQReason,
    create_dlq_envelope,
)


EXPECTED_REASONS = {
    "required_field_missing",
    "invalid_encoding",
    "invalid_unit",
    "incompatible_structure",
    "normalization_failure",
}


def test_dlq_reason_codes_are_registered():
    assert {reason.value for reason in DLQReason} == EXPECTED_REASONS


def test_dlq_envelope_contains_rejection_metadata():
    envelope = create_dlq_envelope(
        event_id="evt-001",
        source_system="endpoint",
        reason_code=DLQReason.INVALID_ENCODING,
        message="payload could not be decoded",
        raw_payload={"data": "bad"},
    )

    assert envelope.to_dict() == {
        "event_id": "evt-001",
        "source_system": "endpoint",
        "reason_code": "invalid_encoding",
        "message": "payload could not be decoded",
        "raw_payload": {"data": "bad"},
    }


def test_dlq_reason_code_is_not_silently_replaced():
    envelope = create_dlq_envelope(
        event_id="evt-002",
        source_system="network",
        reason_code=DLQReason.INVALID_UNIT,
        message="unsupported unit",
        raw_payload={"value": "abc"},
    )

    assert envelope.to_dict()["reason_code"] == "invalid_unit"
    assert envelope.to_dict()["raw_payload"]["value"] == "abc"


def test_dlq_rejects_unknown_reason_code():
    with pytest.raises((ValueError, AttributeError)):
        create_dlq_envelope(
            event_id="evt-003",
            source_system="file",
            reason_code="bad_reason",
            message="invalid",
            raw_payload={},
        )
