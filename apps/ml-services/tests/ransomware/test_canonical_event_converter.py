import pytest

from config.ransomware.shared.canonical_event_converter import (
    convert_to_canonical_event,
)
from config.ransomware.shared.validation.canonical_event_validator import (
    validate_event,
)


@pytest.fixture
def source_record():
    return {
        "id": "evt-converter-001",
        "event_time": "2026-01-01T12:00:00+05:30",
        "ingest_time": "2026-01-01T12:00:05+05:30",
        "schema_version": "1.0",
        "source": "SYNTHETIC",
        "family": "SYNTHETIC",
        "type": "test_event",
        "industry": "ENERGY",
        "site": "ENERGY-BLR01",
        "asset": "ENERGY-BLR01-ASSET-IDENTITY-001",
        "zone": "ENTERPRISE_IT",
        "actor": "N/A",
        "severity": "MEDIUM",
        "attributes": {"description": "test event"},
        "metrics": {"risk_score": "0.5"},
        "quality_flags": ["normalized"],
        "provenance": "SYNTHETIC_TEST",
    }


@pytest.fixture
def field_mapping():
    return {
        "event_id": "id",
        "event_time": "event_time",
        "ingest_time": "ingest_time",
        "schema_version": "schema_version",
        "source_system": "source",
        "event_family": "family",
        "event_type": "type",
        "industry": "industry",
        "site_id": "site",
        "asset_id": "asset",
        "zone": "zone",
        "actor_id": "actor",
        "severity": "severity",
        "attributes": "attributes",
        "metrics": "metrics",
        "quality_flags": "quality_flags",
        "data_provenance": "provenance",
    }


def test_converts_and_validates_canonical_event(source_record, field_mapping):
    event = convert_to_canonical_event(
        source_record,
        field_mapping=field_mapping,
    )

    assert event["event_time"] == "2026-01-01T06:30:00Z"
    assert event["source_system"] == "synthetic"
    assert event["site_id"] == "energy-blr01"
    assert event["actor_id"] is None
    assert event["metrics"] == {"risk_score": 0.5}
    assert len(event["payload_hash"]) == 64
    assert validate_event(event) == []


def test_rejects_missing_mapped_source_field(source_record, field_mapping):
    del source_record["event_time"]

    with pytest.raises(ValueError, match="source field missing"):
        convert_to_canonical_event(
            source_record,
            field_mapping=field_mapping,
        )


def test_rejects_invalid_timestamp(source_record, field_mapping):
    source_record["event_time"] = "2026-01-01T12:00:00"

    with pytest.raises(ValueError):
        convert_to_canonical_event(
            source_record,
            field_mapping=field_mapping,
        )


def test_rejects_invalid_metric(source_record, field_mapping):
    source_record["metrics"] = {"risk_score": "not-a-number"}

    with pytest.raises(ValueError):
        convert_to_canonical_event(
            source_record,
            field_mapping=field_mapping,
        )


def test_rejects_invalid_asset_identifier(source_record, field_mapping):
    source_record["asset"] = "wrong-format"

    with pytest.raises(ValueError, match="asset_id"):
        convert_to_canonical_event(
            source_record,
            field_mapping=field_mapping,
        )


def test_rejects_incomplete_mapping(source_record):
    with pytest.raises(ValueError, match="missing canonical mappings"):
        convert_to_canonical_event(
            source_record,
            field_mapping={"event_id": "id"},
        )


def test_converter_parquet_round_trip_preserves_canonical_event(
    source_record,
    field_mapping,
    tmp_path,
):
    import json

    import pandas as pd

    from config.ransomware.shared.validation.parquet_events import (
        read_canonical_events,
    )

    event = convert_to_canonical_event(
        source_record,
        field_mapping=field_mapping,
    )

    parquet_path = tmp_path / "canonical_event_round_trip.parquet"
    row = dict(event)

    for field in ("attributes", "metrics", "quality_flags"):
        row[field] = json.dumps(row[field])

    pd.DataFrame([row]).to_parquet(parquet_path, index=False)

    restored_events = read_canonical_events(parquet_path)

    assert restored_events == [event]
    assert validate_event(restored_events[0]) == []
