"""Regression tests for synthetic timeline evidence validation."""

import hashlib
import json
from copy import deepcopy

import pytest

from app.services.ransomware_timeline_validation import valid_timeline_evidence


@pytest.fixture
def valid_evidence():
    evidence = {
        "task_id": "RW-120-6",
        "schema_version": "1.0",
        "scenario_id": "rw-attack-070891bdbaec",
        "status": "available",
        "scope": "offline_synthetic_observable_evidence",
        "data_provenance": "synthetic_development",
        "is_operational_incident_timeline": False,
        "event_count": 1,
        "first_event_at": "2026-01-01T06:00:00Z",
        "last_event_at": "2026-01-01T06:00:00Z",
        "observed_asset_ids": ["synthetic-asset-001"],
        "event_family_counts": {"synthetic": 1},
        "sequence_fingerprint_sha256": "a" * 64,
        "fingerprint_scope": "Synthetic event sequence; timestamps excluded.",
        "limitations": "Not a verified operational incident.",
        "timeline": [
            {
                "sequence_index": 0,
                "event_time": "2026-01-01T06:00:00Z",
                "event_family": "synthetic",
                "event_type": "observable_event",
                "asset_id": "synthetic-asset-001",
                "attributes": {"observable_only": True},
            }
        ],
    }

    material = [
        {
            "sequence_index": event["sequence_index"],
            "event_family": event["event_family"],
            "event_type": event["event_type"],
            "asset_id": event["asset_id"],
            "attributes": event["attributes"],
        }
        for event in evidence["timeline"]
    ]

    canonical = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence["sequence_fingerprint_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return evidence


def test_accepts_consistent_synthetic_evidence(valid_evidence):
    assert valid_timeline_evidence(valid_evidence) is True


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b["timeline"][0]["attributes"].update(
            {"nested": {"ground_truth": "attack"}}
        ),
        lambda b: b["timeline"][0]["attributes"].update(
            {"observable_value": float("nan")}
        ),
        lambda b: b.update({"observed_asset_ids": ["wrong-asset"]}),
        lambda b: b.update({"event_family_counts": {"synthetic": 2}}),
        lambda b: b.update({"first_event_at": "2026-01-02T06:00:00Z"}),
        lambda b: b.update({"scope": "operational_incident"}),
        lambda b: b.update({"is_operational_incident_timeline": True}),
        lambda b: b.update({"sequence_fingerprint_sha256": "invalid"}),
        lambda b: b["timeline"][0].update(
            {"event_time": "2026-01-01T06:00:00"}
        ),
        lambda b: b["timeline"][0].update({"sequence_index": True}),
    ],
)
def test_rejects_invalid_evidence(valid_evidence, mutation):
    evidence = deepcopy(valid_evidence)
    mutation(evidence)

    assert valid_timeline_evidence(evidence) is False


def test_rejects_tampered_event_with_original_fingerprint(valid_evidence):
    evidence = deepcopy(valid_evidence)

    # Alter observable evidence without updating its SHA-256 fingerprint.
    evidence["timeline"][0]["attributes"]["observable_only"] = False

    assert valid_timeline_evidence(evidence) is False


def test_rejects_tampered_event_type_with_original_fingerprint(valid_evidence):
    evidence = deepcopy(valid_evidence)

    evidence["timeline"][0]["event_type"] = "modified_observable_event"

    assert valid_timeline_evidence(evidence) is False
