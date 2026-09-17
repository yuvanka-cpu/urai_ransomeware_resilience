import json
from pathlib import Path

from config.ransomware.shared.dlq_contract import DLQReason


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
    / "shared"
    / "schemas"
    / "dlq_event.avsc"
)

FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "tests"
    / "ransomware"
    / "fixtures"
    / "dlq_invalid_unit.json"
)


def test_dlq_schema_has_required_fields():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    fields = {field["name"] for field in schema["fields"]}

    assert fields == {
        "event_id",
        "source_system",
        "reason_code",
        "message",
        "raw_payload",
    }


def test_dlq_schema_contains_all_reason_codes():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    reason_field = next(
        field for field in schema["fields"]
        if field["name"] == "reason_code"
    )

    assert set(reason_field["type"]["symbols"]) == {
        reason.value for reason in DLQReason
    }


def test_dlq_fixture_is_valid():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["event_id"]
    assert fixture["source_system"]
    assert fixture["reason_code"] in {
        reason.value for reason in DLQReason
    }
    assert fixture["message"]
    assert fixture["raw_payload"]
