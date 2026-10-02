from app.schemas.requests import RansomwareRequest
from app.services.ransomware_orchestrator import (
    assemble_orchestration_response,
    build_request_context,
)


REQUEST = RansomwareRequest(
    schema_version="1.0",
    use_case="ransomware_resilience",
    industry="energy",
    site_id="synthetic-site-001",
    site_type="control_centre",
    scenario_id="rw-attack-070891bdbaec",
    observable_input={"login_failures": 3},
)


def test_rw1104_uses_model_decision_without_recomputing_it():
    context = build_request_context(REQUEST)

    response = assemble_orchestration_response(
        REQUEST,
        context,
        {
            "result": {
                "decision": "investigate",
                "bundle_version": "rw0906_v1",
                "probabilities": {"calibrated": 0.2902},
                "components": {
                    "catboost_score": 0.46,
                    "rule_score": 0.10,
                    "anomaly_score": 0.20,
                    "graph_score": 0.72,
                    "temporal_missing": 1,
                },
            }
        },
    )

    assert response["decision"] == "investigate"
    assert response["canonical_contract_complete"] is False
    assert response["recommendation_review_state"] == "pending_review"
    assert response["recommended_actions"]


def test_rw1105_safety_invariants_survive_aggregation():
    context = build_request_context(REQUEST)

    response = assemble_orchestration_response(
        REQUEST,
        context,
        {
            "result": {
                "decision": "high_risk",
                "bundle_version": "rw0906_v1",
                "probabilities": {"calibrated": 0.40},
                "components": {},
            }
        },
    )

    assert response["human_approval_required"] is True
    assert response["real_action_executed"] is False
    assert any("physical safety" in w.lower() for w in response["warnings"])


def test_rw1106_audit_contains_required_trace_context():
    context = build_request_context(REQUEST)

    response = assemble_orchestration_response(
        REQUEST,
        context,
        {
            "_gateway_latency_ms": 42.5,
            "result": {
                "decision": "investigate",
                "bundle_version": "rw0906_v1",
                "probabilities": {"calibrated": 0.29},
                "components": {},
            },
        },
    )

    audit = response["audit"]

    assert audit["request_id"] == context["request_id"]
    assert audit["trace_id"] == context["trace_id"]
    assert audit["scenario_id"] == REQUEST.scenario_id
    assert audit["artifact_versions"] == ["rw0906_v1"]
    assert audit["data_provenance"] == "LIVE_MODEL"
    assert audit["latency_ms"] == 42.5
    assert audit["recommendation_review_state"] == "pending_review"
