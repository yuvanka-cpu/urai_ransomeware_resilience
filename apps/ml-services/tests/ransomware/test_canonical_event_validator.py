import pytest

from config.ransomware.shared.validation.canonical_event_validator import (
    canonical_payload_hash,
    validate_event,
)
from config.ransomware.shared.validation.feature_leakage_guard import (
    validate_deployed_features,
)


def valid_event():
    event = {
        "event_id": "evt-negative-001",
        "event_time": "2026-01-01T06:30:00Z",
        "ingest_time": "2026-01-01T06:30:05Z",
        "schema_version": "1.0",
        "source_system": "synthetic",
        "event_family": "synthetic",
        "event_type": "ransomware_test_event",
        "industry": "energy",
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-identity-001",
        "zone": "enterprise_it",
        "actor_id": None,
        "severity": "medium",
        "attributes": {"test": "negative_fixture"},
        "metrics": {},
        "quality_flags": [],
        "data_provenance": "SYNTHETIC_GROUND_TRUTH",
        "payload_hash": "",
    }

    event["payload_hash"] = canonical_payload_hash(event)

    return event


def test_truth_leakage_fixture_fails():
    with pytest.raises(ValueError):
        validate_deployed_features(["event_type", "is_ransomware"])


def test_non_numeric_metric_fixture_fails():
    event = valid_event()
    event["metrics"] = {"risk_score": "not-a-number"}

    errors = validate_event(event)

    assert any("metrics" in error.lower() for error in errors)


def test_stale_hash_fixture_fails():
    event = valid_event()
    event["payload_hash"] = "b" * 64

    errors = validate_event(event)

    assert "payload_hash: does not match canonical payload" in errors


def test_empty_metric_map_passes_unit_registry():
    event = valid_event()
    assert validate_event(event) == []


def test_unregistered_metric_fails_unit_registry():
    event = valid_event()
    event["metrics"] = {"risk_score": 0.5}
    event["payload_hash"] = canonical_payload_hash(event)

    errors = validate_event(event)

    assert "metrics: unregistered canonical metric 'risk_score'" in errors
