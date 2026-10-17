"""RW-120-6: Protected synthetic observable timeline API tests."""

from fastapi.testclient import TestClient

from config.ransomware import rw1006_internal_api_cycle2 as api


client = TestClient(api.app)

VALID_REQUEST = {
    "schema_version": "1.0",
    "mode": "synthetic_scenario",
    "industry": "energy",
    "site_id": "synthetic-energy-001",
    "site_type": "control_centre",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {},
}


def test_timeline_returns_validated_synthetic_observations():
    response = client.post(
        "/internal/ransomware/observable-timeline",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["schema_version"] == "1.0"
    assert body["task_id"] == "RW-120-6"
    assert body["scenario_id"] == VALID_REQUEST["scenario_id"]
    assert body["status"] == "available"
    assert body["data_provenance"] == "synthetic_development"
    assert body["is_operational_incident_timeline"] is False
    assert body["event_count"] == len(body["timeline"])
    assert body["event_count"] > 0

    assert all(
        "event_time" in item
        and "event_type" in item
        and "asset_id" in item
        for item in body["timeline"]
    )

    assert "ground_truth" not in str(body)
    assert "incident_stage_truth" not in str(body)


def test_timeline_rejects_prohibited_scenario():
    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "scenario_id": "rw-attack-902287f49390",
        },
    )

    assert response.status_code == 404


def test_timeline_rejects_wrong_industry():
    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "industry": "petrochemical",
            "site_type": "refinery",
        },
    )

    assert response.status_code == 422


def test_timeline_rejects_wrong_site_type():
    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "site_type": "refinery",
        },
    )

    assert response.status_code == 422


def test_timeline_rejects_truth_bearing_input():
    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "observable_input": {
                "ground_truth": "attack",
            },
        },
    )

    assert response.status_code == 422


def test_timeline_unavailable_when_event_summary_invalid(monkeypatch):
    from config.ransomware import rw1304_forensic_summary

    monkeypatch.setattr(
        rw1304_forensic_summary,
        "summarize_forensic_events",
        lambda events: {
            "status": "unavailable",
            "reason": "Invalid synthetic event evidence.",
            "scope": "offline_synthetic_observable_evidence",
        },
        raising=False,
    )

    response = client.post(
        "/internal/ransomware/observable-timeline",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert "timeline" not in response.json()
