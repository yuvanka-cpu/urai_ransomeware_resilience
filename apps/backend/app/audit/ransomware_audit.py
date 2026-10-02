from typing import Any


def build_audit_event(
    *,
    request_id: str,
    trace_id: str,
    scenario_id: str,
    artifact_versions: list[str],
    data_provenance: str,
    warnings: list[str],
    latency_ms: float | None,
    recommendation_review_state: str,
) -> dict[str, Any]:
    return {
        "event_type": "ransomware_orchestration",
        "request_id": request_id,
        "trace_id": trace_id,
        "scenario_id": scenario_id,
        "artifact_versions": artifact_versions,
        "data_provenance": data_provenance,
        "warnings": list(warnings),
        "latency_ms": latency_ms,
        "recommendation_review_state": recommendation_review_state,
    }
