import json
from pathlib import Path


SCHEMA = Path(
    "config/ransomware/shared/schemas/canonical_event.avsc"
)

CONTRACT = Path(
    "config/ransomware/shared/schemas/offline_parquet_parity.md"
)


def test_parquet_parity_contract_exists():
    assert CONTRACT.exists()


def test_canonical_schema_is_the_parity_source():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "canonical_event.avsc" in text
    assert "same canonical field definitions" in text


def test_all_canonical_fields_are_documented_for_parquet():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    contract = CONTRACT.read_text(encoding="utf-8")

    for field in schema["fields"]:
        assert f"- {field['name']}" in contract


def test_units_must_remain_aligned():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "same canonical units as the online path" in text
    assert "unit change is a schema evolution event" in text


def test_source_native_fields_cannot_bypass_normalization():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "source-native field names" in text
    assert "bypasses normalization" in text


def test_parity_report_and_snapshot_are_required():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "canonical event Parquet snapshot" in text
    assert "schema parity report" in text


def test_offline_serialization_safety_boundary():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "reproducible analysis and validation" in text
    assert "OT writes" in text
    assert "recovery execution" in text
