"""RW-150-1: Internal ML response validation regression tests."""

from copy import deepcopy

import pytest

from app.services.ransomware_ml_gateway import MLGatewayError
from app.services.ransomware_ml_response_validation import validate_ml_response


SCENARIO_ID = "rw-attack-070891bdbaec"


def valid_response():
    runtime_contract = {
        "synthetic_only": True,
        "human_approval_required": True,
        "real_action_executed": False,
        "operational_state_claimed": False,
        "physical_safety_determination": "not_determined",
    }

    return {
        "schema_version": "1.0",
        "task": "RW-100-6",
        "mode": "synthetic_scenario",
        "request_id": "ml-request-001",
        "trace_id": "ml-trace-001",
        "scenario_id": SCENARIO_ID,
        "bundle_version": "rw0906_v2",
        "result": {
            "bundle_version": "rw0906_v2",
            "decision": "investigate",
            "probabilities": {
                "catboost": 0.42,
                "stacked": 0.45,
                "calibrated": 0.44,
            },
            "components": {
                "rule_score": 0.4,
                "anomaly_score": 0.5,
                "catboost_score": 0.42,
                "graph_score": 0.3,
                "temporal_score": None,
                "temporal_missing": 1,
            },
            "runtime_contract": runtime_contract.copy(),
        },
        "runtime_contract": runtime_contract.copy(),
    }


def test_rw1501_accepts_valid_response():
    response = valid_response()

    validated = validate_ml_response(
        response,
        expected_scenario_id=SCENARIO_ID,
    )

    assert validated == response


@pytest.mark.parametrize(
    "mutation",
    [
        lambda body: body["result"].pop("decision"),
        lambda body: body["result"].update({"decision": "unavailable"}),
        lambda body: body["result"]["probabilities"].update(
            {"calibrated": 1.7}
        ),
        lambda body: body["result"]["probabilities"].update(
            {"calibrated": float("nan")}
        ),
        lambda body: body["result"]["components"].update(
            {"graph_score": -0.2}
        ),
        lambda body: body.update({"scenario_id": "wrong-scenario"}),
        lambda body: body["result"].update(
            {"bundle_version": "different-bundle"}
        ),
        lambda body: body["runtime_contract"].update(
            {"real_action_executed": True}
        ),
        lambda body: body["result"]["runtime_contract"].update(
            {"human_approval_required": False}
        ),
        lambda body: body["result"]["components"].update(
            {"temporal_score": 0.7}
        ),
        lambda body: body["result"]["components"].update(
            {"temporal_missing": 0}
        ),
        lambda body: body.update({"result": {}}),
    ],
)
def test_rw1501_rejects_invalid_response(mutation):
    response = deepcopy(valid_response())
    mutation(response)

    with pytest.raises(MLGatewayError, match="Invalid ML response contract"):
        validate_ml_response(
            response,
            expected_scenario_id=SCENARIO_ID,
        )
