from __future__ import annotations

from fastapi.testclient import TestClient

from config.ransomware.rw1006_internal_api import app


client = TestClient(app)

VALID_REQUEST = {
    "schema_version": "1.0",
    "mode": "synthetic_scenario",
    "industry": "energy",
    "site_id": "demo-site",
    "site_type": "substation",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {},
}


def test_rw1006_health_contract():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "task": "RW-100-6",
        "schema_version": "1.0",
    }


def test_rw1006_synthetic_inference_contract():
    response = client.post(
        "/internal/ransomware/infer",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["schema_version"] == "1.0"
    assert payload["task"] == "RW-100-6"
    assert payload["mode"] == "synthetic_scenario"
    assert payload["scenario_id"] == VALID_REQUEST["scenario_id"]
    assert payload["bundle_version"] == "rw0906_v1"

    result = payload["result"]

    assert result["task"] == "RW-100-3"
    assert result["sector"] == "energy"
    assert result["decision"] in {
        "normal",
        "investigate",
        "high_risk",
    }

    assert "label" not in result
    assert "variant" not in result
    assert "is_ransomware" not in result

    runtime = payload["runtime_contract"]

    assert runtime["synthetic_only"] is True
    assert runtime["human_approval_required"] is True
    assert runtime["real_action_executed"] is False
    assert runtime["operational_state_claimed"] is False
    assert runtime["physical_safety_determination"] == "not_determined"


def test_rw1006_is_deterministic_except_request_trace_ids():
    first = client.post(
        "/internal/ransomware/infer",
        json=VALID_REQUEST,
    )
    second = client.post(
        "/internal/ransomware/infer",
        json=VALID_REQUEST,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["request_id"] != second_payload["request_id"]
    assert first_payload["trace_id"] != second_payload["trace_id"]

    first_payload.pop("request_id")
    first_payload.pop("trace_id")
    second_payload.pop("request_id")
    second_payload.pop("trace_id")

    assert first_payload == second_payload


def test_rw1006_rejects_ground_truth_input():
    request = {
        **VALID_REQUEST,
        "observable_input": {
            "nested": {
                "ground_truth": {
                    "is_ransomware": True,
                }
            }
        },
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_rejects_cross_sector_site():
    request = {
        **VALID_REQUEST,
        "industry": "petrochemical",
        "site_type": "substation",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_rejects_unknown_scenario():
    request = {
        **VALID_REQUEST,
        "scenario_id": "rw-attack-does-not-exist",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 404


def test_rw1006_rejects_extra_request_fields():
    request = {
        **VALID_REQUEST,
        "decision": "high_risk",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422
