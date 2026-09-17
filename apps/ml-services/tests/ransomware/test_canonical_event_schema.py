import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
    / "shared"
    / "schemas"
    / "canonical_event.avsc"
)

CONTRACT_PATH = SCHEMA_PATH.with_name("canonical_event_contract.md")


EXPECTED_FIELDS = {
    "event_id",
    "event_time",
    "ingest_time",
    "schema_version",
    "source_system",
    "event_family",
    "event_type",
    "industry",
    "site_id",
    "asset_id",
    "zone",
    "actor_id",
    "severity",
    "attributes",
    "metrics",
    "quality_flags",
    "data_provenance",
    "payload_hash",
}


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_canonical_event_schema_exists_and_is_valid_json():
    schema = load_schema()

    assert schema["type"] == "record"
    assert schema["name"] == "CanonicalRansomwareEvent"
    assert schema["namespace"] == "urai.ransomware"


def test_canonical_event_contains_required_envelope_fields():
    schema = load_schema()
    fields = {field["name"] for field in schema["fields"]}

    assert fields == EXPECTED_FIELDS


def test_canonical_event_has_expected_core_types():
    schema = load_schema()
    fields = {field["name"]: field["type"] for field in schema["fields"]}

    assert fields["event_id"] == "string"
    assert fields["event_time"] == "string"
    assert fields["ingest_time"] == "string"
    assert fields["schema_version"] == "string"
    assert fields["site_id"] == "string"
    assert fields["asset_id"] == "string"
    assert fields["severity"] == "string"
    assert fields["data_provenance"] == "string"
    assert fields["payload_hash"] == "string"


def test_actor_id_is_optional_with_null_default():
    schema = load_schema()
    actor_id = next(
        field for field in schema["fields"] if field["name"] == "actor_id"
    )

    assert actor_id["type"] == ["null", "string"]
    assert actor_id["default"] is None


def test_attributes_metrics_and_quality_flags_are_structured():
    schema = load_schema()
    fields = {field["name"]: field["type"] for field in schema["fields"]}

    assert fields["attributes"] == {
        "type": "map",
        "values": "string",
    }
    assert fields["metrics"] == {
        "type": "map",
        "values": "double",
    }
    assert fields["quality_flags"] == {
        "type": "array",
        "items": "string",
    }


def test_human_readable_contract_exists():
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "# Canonical Observable Event Contract" in contract
    assert "`event_id`" in contract
    assert "`payload_hash`" in contract
    assert "Normalization rules" in contract
    assert "Safety boundary" in contract
