from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.ransomware_ml_gateway import MLGatewayError


client = TestClient(app)

VALID_PAYLOAD = {
    "schema_version": "1.0",
    "use_case": "ransomware_resilience",
    "industry": "energy",
    "site_id": "synthetic-site-001",
    "site_type": "control_centre",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {"login_failures": 3},
}


@patch(
    "app.routes.ransomware.run_ml_inference",
    side_effect=MLGatewayError("ML service timeout after retry policy"),
)
def test_rw1107_route_returns_explicit_unavailable_on_ml_failure(mock_run_ml):
    response = client.post(
        "/api/v1/ransomware/infer",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["decision"] == "unavailable"
    assert body["runtime_state"] == "unavailable"
    assert body["data_provenance"] == "UNAVAILABLE"
    assert body["fallback_is_live_inference"] is False
    assert body["human_approval_required"] is True
    assert body["real_action_executed"] is False
    assert "ML service timeout after retry policy" in body["warnings"]
    assert body["request_id"]
    assert body["trace_id"]
    mock_run_ml.assert_called_once()


@patch(
    "app.routes.ransomware.run_ml_inference",
    side_effect=MLGatewayError("ML service dependency unavailable"),
)
def test_rw1107_route_never_substitutes_success_on_dependency_failure(
    mock_run_ml,
):
    response = client.post(
        "/api/v1/ransomware/infer",
        json=VALID_PAYLOAD,
    )

    body = response.json()

    assert body["decision"] == "unavailable"
    assert body["data_provenance"] != "LIVE_MODEL"
    assert body["runtime_state"] != "live_model"
    assert "ML service dependency unavailable" in body["warnings"]
    mock_run_ml.assert_called_once()
