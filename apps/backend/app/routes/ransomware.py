from fastapi import APIRouter

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