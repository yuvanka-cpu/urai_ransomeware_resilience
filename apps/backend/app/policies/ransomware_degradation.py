from typing import Any


def build_degraded_state(
    *,
    reason: str,
    request_id: str,
    trace_id: str,
) -> dict[str, Any]:
    return {
        "state": "degraded",
        "runtime_state": "degraded",
        "decision": "unavailable",
        "data_provenance": "UNAVAILABLE",
        "request_id": request_id,
        "trace_id": trace_id,
        "warnings": [reason],
        "fallback_is_live_inference": False,
        "human_approval_required": True,
        "real_action_executed": False,
    }


def build_fallback_state(
    *,
    reason: str,
    request_id: str,
    trace_id: str,
) -> dict[str, Any]:
    return {
        "state": "fallback",
        "runtime_state": "fallback",
        "decision": "unavailable",
        "data_provenance": "FALLBACK",
        "request_id": request_id,
        "trace_id": trace_id,
        "warnings": [
            reason,
            "FALLBACK: live-model output is unavailable.",
        ],
        "fallback_is_live_inference": False,
        "human_approval_required": True,
        "real_action_executed": False,
    }


def build_unavailable_state(
    *,
    reason: str,
    request_id: str,
    trace_id: str,
) -> dict[str, Any]:
    return {
        "state": "unavailable",
        "runtime_state": "unavailable",
        "decision": "unavailable",
        "data_provenance": "UNAVAILABLE",
        "request_id": request_id,
        "trace_id": trace_id,
        "warnings": [reason],
        "fallback_is_live_inference": False,
        "human_approval_required": True,
        "real_action_executed": False,
    }
