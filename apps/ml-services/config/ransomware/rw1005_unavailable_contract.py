"""RW-100-5 explicit unavailable runtime contract.

Synthetic ransomware-resilience PoC only.

Any required runtime, artifact, feature, or safety-contract failure blocks
the model decision. No fallback artifact or silent substitution is allowed.
"""

from __future__ import annotations

from typing import Any

from config.ransomware.rw0905_artifact_availability import (
    ArtifactStatus,
    FailureReason,
    validate_artifact,
)


REQUIRED_FAILURE_REASONS = {
    FailureReason.MISSING.value,
    FailureReason.CORRUPT.value,
    FailureReason.STALE.value,
    FailureReason.INCOMPATIBLE.value,
    FailureReason.SLOW.value,
}


def build_unavailable_result(
    *,
    artifact_id: str,
    failure_reason: str,
    detail: str,
    component_status: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build the canonical unavailable result.

    No decision, severity, confidence, fallback artifact, or operational
    conclusion is inferred when a required runtime dependency fails.
    """

    if failure_reason not in REQUIRED_FAILURE_REASONS:
        raise ValueError(
            f"Unsupported unavailable failure reason: {failure_reason}"
        )

    if not artifact_id:
        raise ValueError("artifact_id must be non-empty")

    if not detail:
        raise ValueError("detail must be non-empty")

    statuses = dict(component_status or {})
    statuses[artifact_id] = "unavailable"

    result_warnings = list(warnings or [])
    result_warnings.append(
        f"Runtime unavailable: {artifact_id} failed with {failure_reason}."
    )
    result_warnings.append(detail)
    result_warnings.append(
        "No alternate artifact or model was silently substituted."
    )

    return {
        "decision": "unavailable",
        "incident_stage": "none",
        "confidence": None,
        "severity": "low",
        "artifact_status": "unavailable",
        "artifact_provenance": [
            {
                "artifact_id": artifact_id,
                "status": "unavailable",
                "failure_reason": failure_reason,
            }
        ],
        "component_status": statuses,
        "warnings": result_warnings,
        "human_approval_required": True,
        "real_action_executed": False,
        "operational_state_claimed": False,
        "physical_safety_determination": "not_determined",
        "silent_substitution": False,
        "replacement_artifact_not_selected": True,
    }


def unavailable_from_artifact_health(
    health: Any,
    *,
    component_status: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Convert RW-090-5 ArtifactHealth into the RW-100-5 contract."""

    if health.status is ArtifactStatus.AVAILABLE:
        raise ValueError(
            "unavailable_from_artifact_health requires an unavailable artifact"
        )

    return build_unavailable_result(
        artifact_id=health.artifact_id,
        failure_reason=health.failure_reason.value,
        detail=health.detail,
        component_status=component_status,
        warnings=warnings,
    )


def validate_required_artifact(
    *,
    artifact_id: str,
    path: Any,
    expected_sha256: str | None = None,
    expected_schema_version: str | None = None,
    actual_schema_version: str | None = None,
    artifact_age_seconds: float | None = None,
    latency_ms: float | None = None,
) -> dict[str, Any]:
    """Validate an artifact and return available/unavailable runtime state."""

    health = validate_artifact(
        artifact_id=artifact_id,
        path=path,
        expected_sha256=expected_sha256,
        expected_schema_version=expected_schema_version,
        actual_schema_version=actual_schema_version,
        artifact_age_seconds=artifact_age_seconds,
        latency_ms=latency_ms,
    )

    if health.status is ArtifactStatus.AVAILABLE:
        return {
            "status": "available",
            "artifact_id": artifact_id,
            "failure_reason": "none",
            "component_status": {
                artifact_id: "available",
            },
        }

    return unavailable_from_artifact_health(health)


def main() -> None:
    print("=== RW-100-5 UNAVAILABLE CONTRACT ===")
    print("Missing: unavailable")
    print("Corrupt: unavailable")
    print("Stale: unavailable")
    print("Incompatible: unavailable")
    print("Slow: unavailable")
    print("Silent substitution: forbidden")
    print("Human approval required: True")
    print("Real action executed: False")
    print("Physical safety determination: not_determined")
    print("Status: unavailable contract ready")


if __name__ == "__main__":
    main()
