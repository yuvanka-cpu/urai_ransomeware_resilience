from unittest.mock import patch

from app.schemas.requests import RansomwareRequest
from app.services.ransomware_orchestrator import build_ml_payload, run_ml_inference


VALID_REQUEST = RansomwareRequest(
    schema_version="1.0",
    use_case="ransomware_resilience",
    industry="energy",
    site_id="synthetic-site-001",
    site_type="control_centre",
    scenario_id="rw-attack-070891bdbaec",
    observable_input={"login_failures": 3, "network_anomaly": False},
)


def test_rw1103_builds_internal_ml_payload():
    context = {
        "request_id": "rw-request-001",
        "trace_id": "trace-001",
    }

    payload = build_ml_payload(VALID_REQUEST, context)

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "synthetic_scenario"
    assert payload["industry"] == "energy"
    assert payload["site_id"] == "synthetic-site-001"
    assert payload["site_type"] == "control_centre"
    assert payload["scenario_id"] == "rw-attack-070891bdbaec"
    assert payload["observable_input"]["login_failures"] == 3


@patch("app.services.ransomware_orchestrator.call_ml_service")
def test_rw1103_passes_correlation_context_to_ml_gateway(mock_call):
    mock_call.return_value = {
        "request_id": "ml-request-001",
        "trace_id": "ml-trace-001",
        "result": {"decision": "investigate"},
    }

    context = {
        "request_id": "rw-request-001",
        "trace_id": "trace-001",
    }

    result = run_ml_inference(VALID_REQUEST, context)

    mock_call.assert_called_once()
    call = mock_call.call_args
    assert call.kwargs["request_id"] == "rw-request-001"
    assert call.kwargs["trace_id"] == "trace-001"
    assert result["result"]["decision"] == "investigate"
