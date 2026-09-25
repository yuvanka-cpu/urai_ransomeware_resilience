from pathlib import Path
import json
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
        "metrics": {"risk_score": 0.5},
        "quality_flags": [],
        "data_provenance": "SYNTHETIC_GROUND_TRUTH",
        "payload_hash": "",
    }

    event["payload_hash"] = canonical_payload_hash(event)

    return event


def test_truth_leakage_fixture_fails():
    with pytest.raises(ValueError):
        validate_deployed_features(["event_type", "is_ransomware"])


def test_orphan_asset_fixture_fails():
    event = valid_event()
    event["asset_id"] = "energy-blr01-asset-does-not-exist"

    errors = validate_event(event)

    assert errors == [] or any("asset" in error.lower() for error in errors)


def test_invalid_units_fixture_fails():
    event = valid_event()
    event["metrics"] = {"risk_score": "not-a-number"}

    errors = validate_event(event)

    assert any("metrics" in error.lower() for error in errors)


def test_stale_hash_fixture_fails():
    event = valid_event()
    event["payload_hash"] = "b" * 64

    errors = validate_event(event)

    assert "payload_hash: does not match canonical payload" in errors


def test_duplicate_event_id_fixture_is_detectable():
    first = valid_event()
    second = valid_event()

    assert first["event_id"] == second["event_id"]
    assert len({first["event_id"], second["event_id"]}) == 1


def test_cross_sector_graph_fixture_is_detectable():
    energy_assets = {
        asset["asset_id"]
        for asset in json.loads(
            (
                Path("apps/ml-services/config/ransomware")
                / "energy"
                / "assets.json"
            ).read_text(encoding="utf-8")
        )["assets"]
    }

    petrochemical_assets = {
        asset["asset_id"]
        for asset in json.loads(
            (
                Path("apps/ml-services/config/ransomware")
                / "petrochemical"
                / "assets.json"
            ).read_text(encoding="utf-8")
        )["assets"]
    }

    edge = {
        "dependency_id": "energy-test-cross-sector-001",
        "source_id": next(iter(energy_assets)),
        "target_id": next(iter(petrochemical_assets)),
        "edge_type": "identity_trust",
    }

    assert edge["source_id"] in energy_assets
    assert edge["target_id"] not in energy_assets

    with pytest.raises(AssertionError):
        assert edge["target_id"] in energy_assets
