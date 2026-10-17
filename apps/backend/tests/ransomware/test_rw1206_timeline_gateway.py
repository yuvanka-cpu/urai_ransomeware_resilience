"""Regression tests for the read-only synthetic timeline gateway."""

from unittest.mock import Mock

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.routes import ransomware_timeline as timeline_route


client = TestClient(app)

VALID_REQUEST = {
    "schema_version": "1.0",
    "use_case": "ransomware_resilience",
    "industry": "energy",
    "site_id": "synthetic-energy-001",
    "site_type": "control_centre",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {},
}

ENDPOINT = "/api/v1/ransomware/observable-timeline"


def test_backend_rejects_prohibited_scenario():
    payload = {
        **VALID_REQUEST,
        "scenario_id": "rw-attack-902287f49390",
    }

    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == 400


def test_backend_rejects_truth_input():
    payload = {
        **VALID_REQUEST,
        "observable_input": {"ground_truth": "attack"},
    }

    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == 422


def test_backend_rejects_wrong_sector_site_type():
    payload = {
        **VALID_REQUEST,
        "site_type": "refinery",
    }

    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == 422


def test_backend_returns_unavailable_for_dependency_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("Synthetic dependency offline")

    monkeypatch.setattr(httpx.Client, "post", fail)

    response = client.post(ENDPOINT, json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert response.json()["timeline"] == []


def test_backend_rejects_mismatched_scenario_response(monkeypatch):
    def fake_post(*args, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "schema_version": "1.0",
                "task_id": "RW-120-6",
                "scenario_id": "wrong-scenario",
                "data_provenance": "synthetic_development",
                "is_operational_incident_timeline": False,
                "status": "available",
                "event_count": 1,
                "timeline": [{"sequence_index": 0}],
            },
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    response = client.post(ENDPOINT, json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_backend_rejects_malformed_event_count(monkeypatch):
    def fake_post(*args, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "schema_version": "1.0",
                "task_id": "RW-120-6",
                "scenario_id": VALID_REQUEST["scenario_id"],
                "data_provenance": "synthetic_development",
                "is_operational_incident_timeline": False,
                "status": "available",
                "event_count": 2,
                "timeline": [{"sequence_index": 0}],
            },
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    response = client.post(ENDPOINT, json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_timeline_event_validator_accepts_valid_events():
    events = [
        {
            "sequence_index": 0,
            "event_time": "2026-01-01T06:00:00Z",
            "event_family": "synthetic",
            "event_type": "observable_event",
            "asset_id": "synthetic-asset-001",
            "attributes": {"observable_only": True},
        },
        {
            "sequence_index": 1,
            "event_time": "2026-01-01T06:01:00Z",
            "event_family": "network",
            "event_type": "connection_observable",
            "asset_id": "synthetic-asset-002",
            "attributes": {},
        },
    ]

    assert timeline_route.valid_timeline_events(events) is True


def test_timeline_event_validator_rejects_malformed_events():
    valid_event = {
        "sequence_index": 0,
        "event_time": "2026-01-01T06:00:00Z",
        "event_family": "synthetic",
        "event_type": "observable_event",
        "asset_id": "synthetic-asset-001",
        "attributes": {"observable_only": True},
    }

    invalid_cases = [
        [{**valid_event, "sequence_index": True}],
        [{**valid_event, "sequence_index": 1}],
        [{**valid_event, "event_time": "invalid-date"}],
        [{**valid_event, "event_time": "2026-01-01T06:00:00"}],
        [{**valid_event, "event_family": ""}],
        [{**valid_event, "event_type": None}],
        [{**valid_event, "asset_id": "   "}],
        [{**valid_event, "attributes": []}],
        [
            valid_event,
            {
                **valid_event,
                "sequence_index": 1,
                "event_time": "2026-01-01T05:59:00Z",
            },
        ],
        [valid_event, valid_event],
    ]

    for events in invalid_cases:
        assert timeline_route.valid_timeline_events(events) is False, (
            f"Malformed timeline was accepted: {events}"
        )
