"""RW-150-1: Validate internal ML responses before live-model orchestration."""

import math
from typing import Any

from app.services.ransomware_ml_gateway import MLGatewayError


VALID_DECISIONS = {"normal", "investigate", "high_risk"}
REQUIRED_PROBABILITIES = ("catboost", "stacked", "calibrated")
REQUIRED_COMPONENTS = (
    "rule_score",
    "anomaly_score",
    "catboost_score",
    "graph_score",
)


def _invalid(reason: str) -> None:
    raise MLGatewayError(f"Invalid ML response contract: {reason}")


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        _invalid(f"{name} must be an object")
    return value


def _nonblank(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _invalid(f"{name} must be a nonblank string")
    return value


def _probability(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _invalid(f"{name} must be numeric")

    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        _invalid(f"{name} must be finite and within [0, 1]")


def validate_ml_response(
    response: Any,
    *,
    expected_scenario_id: str,
) -> dict:
    body = _object(response, "response")

    if body.get("schema_version") != "1.0":
        _invalid("schema_version mismatch")

    if body.get("task") != "RW-100-6":
        _invalid("task mismatch")

    if body.get("mode") != "synthetic_scenario":
        _invalid("mode mismatch")

    if body.get("scenario_id") != expected_scenario_id:
        _invalid("scenario_id mismatch")

    _nonblank(body.get("request_id"), "request_id")
    _nonblank(body.get("trace_id"), "trace_id")

    bundle_version = _nonblank(body.get("bundle_version"), "bundle_version")

    result = _object(body.get("result"), "result")

    if result.get("bundle_version") != bundle_version:
        _invalid("bundle_version mismatch")

    if result.get("decision") not in VALID_DECISIONS:
        _invalid("invalid live-model decision")

    probabilities = _object(result.get("probabilities"), "probabilities")

    for name in REQUIRED_PROBABILITIES:
        _probability(probabilities.get(name), f"probabilities.{name}")

    components = _object(result.get("components"), "components")

    for name in REQUIRED_COMPONENTS:
        _probability(components.get(name), f"components.{name}")

    if components.get("temporal_missing") != 1:
        _invalid("temporal_missing must equal 1")

    if components.get("temporal_score") is not None:
        _invalid("unavailable temporal_score must be null")

    runtime = _object(result.get("runtime_contract"), "result.runtime_contract")
    outer_runtime = _object(body.get("runtime_contract"), "runtime_contract")

    if runtime != outer_runtime:
        _invalid("runtime_contract mismatch")

    required_safety = {
        "synthetic_only": True,
        "human_approval_required": True,
        "real_action_executed": False,
        "operational_state_claimed": False,
        "physical_safety_determination": "not_determined",
    }

    for name, expected in required_safety.items():
        if type(runtime.get(name)) is not type(expected):
            _invalid(f"invalid runtime_contract.{name}")

        if runtime[name] != expected:
            _invalid(f"unsafe runtime_contract.{name}")

    return body
