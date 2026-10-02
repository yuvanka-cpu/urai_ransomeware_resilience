from fastapi import APIRouter, HTTPException

from app.policies.ransomware_degradation import build_unavailable_state
from app.policies.ransomware_policy import validate_synthetic_request
from app.schemas.requests import RansomwareRequest
from app.services.ransomware_ml_gateway import MLGatewayError
from app.services.ransomware_orchestrator import (
    assemble_orchestration_response,
    build_request_context,
    run_ml_inference,
)

from app.services.ransomware_mock import (
    get_normal_response,
    get_investigate_response,
    get_high_risk_response,
    get_unavailable_response,
    get_fallback_response,
)


router = APIRouter()


@router.get("/mock/normal")
def normal_response():
    return get_normal_response()


@router.get("/mock/investigate")
def investigate_response():
    return get_investigate_response()


@router.get("/mock/high-risk")
def high_risk_response():
    return get_high_risk_response()


@router.get("/mock/unavailable")
def unavailable_response():
    return get_unavailable_response()


@router.get("/mock/fallback")
def fallback_response():
    return get_fallback_response()


@router.post("/api/v1/ransomware/infer")
def ransomware_infer(request: RansomwareRequest):
    try:
        validate_synthetic_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    context = build_request_context(request)

    try:
        ml_response = run_ml_inference(request, context)
    except MLGatewayError as exc:
        return {
            **context,
            **build_unavailable_state(
                reason=str(exc),
                request_id=context["request_id"],
                trace_id=context["trace_id"],
            ),
        }

    orchestration = assemble_orchestration_response(
        request,
        context,
        ml_response,
    )

    return {
        **context,
        **orchestration,
    }
