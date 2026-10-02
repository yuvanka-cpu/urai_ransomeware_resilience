from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


VALID_PAYLOAD = {
    "schema_version": "1.0",
    "use_case": "ransomware_resilience",
    "industry": "energy",
    "site_id": "synthetic-site-001",
    "site_type": "control_centre",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {
        "login_failures": 3,
        "network_anomaly": False,
    },
}


@patch(
    "app.routes.ransomware.run_ml_inference",
    return_value={
        "result": {
            "decision": "investigate",
            "bundle_version": "rw0906_v1",
            "probabilities": {"calibrated": 0.2902},
            "components": {},
        }
    },
)
def test_rw1101_versioned_route_accepts_valid_request(mock_run_ml):
    response = client.post("/api/v1/ransomware/infer", json=VALID_PAYLOAD)

    assert response.status_code == 200

    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["task_id"] == "RW-110-1"
    assert body["use_case"] == "ransomware_resilience"
    assert body["industry"] == "energy"
    assert body["site_id"] == "synthetic-site-001"
    assert body["site_type"] == "control_centre"
    assert body["scenario_id"] == "rw-attack-070891bdbaec"
    assert body["request_id"].startswith("rw-")
    assert body["trace_id"].startswith("trace-")


def test_rw1101_route_rejects_unknown_request_fields():
    payload = {
        **VALID_PAYLOAD,
        "unexpected_field": "must_be_rejected",
    }

    response = client.post("/api/v1/ransomware/infer", json=payload)

    assert response.status_code == 422


def test_rw1101_route_rejects_invalid_schema_version():
    payload = {
        **VALID_PAYLOAD,
        "schema_version": "2.0",
    }

    response = client.post("/api/v1/ransomware/infer", json=payload)

    assert response.status_code == 422


def test_rw1102_route_rejects_unpermitted_synthetic_scenario():
    payload = {
        **VALID_PAYLOAD,
        "scenario_id": "rw-not-permitted",
    }

    response = client.post("/api/v1/ransomware/infer", json=payload)

    assert response.status_code == 400
    assert "synthetic scenario is not permitted" in response.json()["detail"]


def test_rw1102_route_rejects_invalid_energy_site_context():
    payload = {
        **VALID_PAYLOAD,
        "site_type": "refinery",
    }

    response = client.post("/api/v1/ransomware/infer", json=payload)

    # Request schema rejects the invalid sector/site pairing before policy.
    assert response.status_code == 422
