import json
from pathlib import Path

import pytest

from config.ransomware.shared.dlq_contract import (
    DLQReason,
    create_dlq_envelope,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "ransomware"
    / "shared"
    / "schemas"
    / "dlq_event.avsc"
)

EXPECTED_REASONS = {
    reason.value for reason in DLQReason
}


@pytest.mark.parametrize("reason", sorted(EXPECTED_REASONS))
def test_dlq_failure_fixture_matches_schema_and_contract(reason):
    fixture_path = FIXTURE_DIR / f"dlq_{reason}.json"

    assert fixture_path.is_file(), (
        f"Missing DLQ fixture for {reason}"
    )

    fixture = json.loads(
        fixture_path.read_text(encoding="utf-8")
    )

    schema = json.loads(
        SCHEMA_PATH.read_text(encoding="utf-8")
    )

    schema_fields = {
        field["name"]: field["type"]
        for field in schema["fields"]
    }

    assert set(fixture) == set(schema_fields)

    assert fixture["reason_code"] == reason
    assert fixture["reason_code"] in EXPECTED_REASONS

    for field in (
        "event_id",
        "source_system",
        "message",
        "raw_payload",
    ):
        assert isinstance(fixture[field], str)
        assert fixture[field]

    json.loads(fixture["raw_payload"])

    envelope = create_dlq_envelope(
        event_id=fixture["event_id"],
        source_system=fixture["source_system"],
        reason_code=DLQReason(reason),
        message=fixture["message"],
        raw_payload=fixture["raw_payload"],
    )

    assert envelope.to_dict() == fixture


def test_dlq_fixture_set_covers_every_registered_failure_reason():
    fixture_reasons = {
        path.stem.removeprefix("dlq_")
        for path in FIXTURE_DIR.glob("dlq_*.json")
    }

    assert fixture_reasons == EXPECTED_REASONS
