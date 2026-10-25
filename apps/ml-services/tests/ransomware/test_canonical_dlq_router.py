import copy
import hashlib
import json

from config.ransomware.shared.dlq_contract import DLQReason
from config.ransomware.shared.validation.canonical_dlq_router import (
    route_canonical_event,
)
from config.ransomware.shared.validation.canonical_event_validator import (
    canonical_payload_hash,
)


def valid_event():
    event = {
        "event_id": "energy-event-001",
        "event_time": "2026-10-25T12:00:00Z",
        "ingest_time": "2026-10-25T12:00:01Z",
        "schema_version": "1.0",
        "source_system": "synthetic",
        "event_family": "synthetic",
        "event_type": "test_event",
        "industry": "energy",
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-historian-001",
        "zone": "enterprise_it",
        "severity": "low",
        "attributes": {},
        "metrics": {},
        "quality_flags": [],
        "data_provenance": "synthetic_test_fixture",
        "payload_hash": "",
    }
    event["payload_hash"] = canonical_payload_hash(event)
    return event


def test_valid_event_is_returned_without_dlq():
    event = valid_event()

    accepted, rejected = route_canonical_event(event)

    assert accepted == event
    assert rejected is None


def test_missing_required_field_routes_to_dlq():
    event = valid_event()
    event.pop("event_id")

    accepted, rejected = route_canonical_event(event)

    assert accepted is None
    assert rejected is not None
    assert rejected.reason_code is DLQReason.REQUIRED_FIELD_MISSING
    assert "missing required field: event_id" in rejected.message


def test_incompatible_structure_routes_to_dlq():
    accepted, rejected = route_canonical_event(["not", "an", "event"])

    assert accepted is None
    assert rejected is not None
    assert rejected.reason_code is DLQReason.INCOMPATIBLE_STRUCTURE


def test_rejected_evidence_is_preserved_without_mutating_input():
    event = valid_event()
    event["unexpected_field"] = "preserve-me"
    original = copy.deepcopy(event)

    accepted, rejected = route_canonical_event(event)

    assert accepted is None
    assert rejected is not None
    assert event == original
    assert json.loads(rejected.raw_payload) == original
    assert "preserve-me" in rejected.raw_payload


def test_invalid_metric_routes_to_normalization_failure():
    event = valid_event()
    event["metrics"] = {"risk_score": "not-a-number"}
    event["payload_hash"] = canonical_payload_hash(event)

    accepted, rejected = route_canonical_event(event)

    assert accepted is None
    assert rejected is not None
    assert rejected.reason_code is DLQReason.NORMALIZATION_FAILURE
    assert "metrics: keys must be strings and values numeric" in rejected.message


def test_other_validation_errors_are_not_silently_repaired():
    event = valid_event()
    event["severity"] = "unknown"
    original = copy.deepcopy(event)

    accepted, rejected = route_canonical_event(event)

    assert accepted is None
    assert rejected is not None
    assert rejected.reason_code is DLQReason.INCOMPATIBLE_STRUCTURE
    assert "severity: invalid canonical severity" in rejected.message
    assert event == original
