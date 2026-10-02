from uuid import uuid4

from app.schemas.requests import RansomwareRequest
from app.services.ransomware_ml_gateway import call_ml_service


API_SCHEMA_VERSION = "1.0"
TASK_ID = "RW-110-1"


def build_request_context(request: RansomwareRequest) -> dict:
    return {
        "schema_version": API_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "request_id": f"rw-{uuid4().hex}",
        "trace_id": f"trace-{uuid4().hex}",
        "use_case": request.use_case,
        "industry": request.industry,
        "site_id": request.site_id,
        "site_type": request.site_type,
        "scenario_id": request.scenario_id,
        "observable_input": request.observable_input,
    }


def build_ml_payload(
    request: RansomwareRequest,
    context: dict,
) -> dict:
    return {
        "schema_version": API_SCHEMA_VERSION,
        "mode": "synthetic_scenario",
        "industry": request.industry.value,
        "site_id": request.site_id,
        "site_type": request.site_type.value,
        "scenario_id": request.scenario_id,
        "observable_input": request.observable_input,
    }


def run_ml_inference(
    request: RansomwareRequest,
    context: dict,
) -> dict:
    payload = build_ml_payload(request, context)

    return call_ml_service(
        payload,
        request_id=context["request_id"],
        trace_id=context["trace_id"],
    )


def assemble_orchestration_response(
    request: RansomwareRequest,
    context: dict,
    ml_response: dict,
) -> dict:
    from app.audit.ransomware_audit import build_audit_event
    from app.policies.ransomware_recommendations import assemble_recommendations
    from app.policies.ransomware_safety import enforce_safety_invariants

    model_result = dict(ml_response["result"])
    probabilities = model_result.get("probabilities", {})
    components = model_result.get("components", {})

    evidence = [
        f"calibrated_probability={probabilities.get('calibrated')}",
        f"catboost_score={components.get('catboost_score')}",
        f"rule_score={components.get('rule_score')}",
        f"anomaly_score={components.get('anomaly_score')}",
        f"graph_score={components.get('graph_score')}",
    ]

    warnings = [
        "Synthetic defensive analysis only; physical safety is not determined."
    ]

    if components.get("temporal_missing") == 1:
        warnings.append(
            "Temporal challenger unavailable; calibrated result excludes it."
        )

    result = {
        "schema_version": API_SCHEMA_VERSION,
        "task_id": "RW-110-1",
        "request_id": context["request_id"],
        "trace_id": context["trace_id"],
        "scenario_id": request.scenario_id,
        "industry": request.industry.value,
        "site_id": request.site_id,
        "site_type": request.site_type.value,
        "runtime_state": "live_model",
        "artifact_status": "loaded",
        "data_provenance": "LIVE_MODEL",
        "decision": model_result["decision"],
        "model_result": model_result,
        "recommendation_review_state": "pending_review",
        "recommended_actions": assemble_recommendations(
            decision=model_result["decision"],
            evidence=evidence,
        ),
        "human_approval_required": True,
        "real_action_executed": False,
        "warnings": warnings,
        "canonical_contract_complete": False,
        "canonical_contract_warning": (
            "RW-1006 does not currently emit incident_stage, severity, "
            "resilience_score, or full asset/recovery context; no backend "
            "value is fabricated for these fields."
        ),
    }

    enforce_safety_invariants(result)

    latency_ms = ml_response.get("_gateway_latency_ms")

    result["audit"] = build_audit_event(
        request_id=context["request_id"],
        trace_id=context["trace_id"],
        scenario_id=request.scenario_id,
        artifact_versions=[model_result["bundle_version"]],
        data_provenance="LIVE_MODEL",
        warnings=result["warnings"],
        latency_ms=latency_ms,
        recommendation_review_state="pending_review",
    )

    return result
