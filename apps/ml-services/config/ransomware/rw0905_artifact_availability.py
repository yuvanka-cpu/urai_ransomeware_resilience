"""RW-090-5 artifact availability and unavailable-behavior contract.

Synthetic ransomware-resilience PoC only.

This module validates whether a promoted artifact is safe to use at runtime.
Any artifact failure produces an explicit unavailable state. No alternate model
or artifact is silently substituted.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


DEFAULT_MAX_AGE_SECONDS = 24 * 60 * 60
DEFAULT_MAX_LATENCY_MS = 1000


class ArtifactStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class FailureReason(str, Enum):
    NONE = "none"
    MISSING = "missing"
    CORRUPT = "corrupt"
    STALE = "stale"
    INCOMPATIBLE = "incompatible"
    SLOW = "slow"


@dataclass(frozen=True)
class ArtifactHealth:
    artifact_id: str
    status: ArtifactStatus
    failure_reason: FailureReason
    detail: str
    substitution_performed: bool
    human_approval_required: bool = True
    real_action_executed: bool = False

    @property
    def usable(self) -> bool:
        return self.status is ArtifactStatus.AVAILABLE


def _unavailable(
    artifact_id: str,
    reason: FailureReason,
    detail: str,
) -> ArtifactHealth:
    return ArtifactHealth(
        artifact_id=artifact_id,
        status=ArtifactStatus.UNAVAILABLE,
        failure_reason=reason,
        detail=detail,
        substitution_performed=False,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_artifact(
    *,
    artifact_id: str,
    path: Path,
    expected_sha256: str | None = None,
    expected_schema_version: str | None = None,
    actual_schema_version: str | None = None,
    artifact_age_seconds: float | None = None,
    latency_ms: float | None = None,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    max_latency_ms: float = DEFAULT_MAX_LATENCY_MS,
) -> ArtifactHealth:
    """Validate one artifact without substituting another artifact.

    Validation order is deterministic:
    missing -> corrupt -> incompatible -> stale -> slow -> available.
    """

    if not artifact_id:
        raise ValueError("artifact_id must be non-empty")

    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")

    if max_latency_ms <= 0:
        raise ValueError("max_latency_ms must be positive")

    if not path.exists():
        return _unavailable(
            artifact_id,
            FailureReason.MISSING,
            f"Artifact does not exist: {path}",
        )

    if not path.is_file():
        return _unavailable(
            artifact_id,
            FailureReason.CORRUPT,
            f"Artifact path is not a regular file: {path}",
        )

    if expected_sha256 is not None:
        actual_sha256 = _sha256(path)
        if actual_sha256.lower() != expected_sha256.lower():
            return _unavailable(
                artifact_id,
                FailureReason.CORRUPT,
                "Artifact SHA-256 checksum does not match the expected value.",
            )

    if (
        expected_schema_version is not None
        and actual_schema_version != expected_schema_version
    ):
        return _unavailable(
            artifact_id,
            FailureReason.INCOMPATIBLE,
            (
                "Artifact schema version is incompatible: "
                f"expected={expected_schema_version!r}, "
                f"actual={actual_schema_version!r}."
            ),
        )

    if artifact_age_seconds is not None:
        if artifact_age_seconds < 0:
            raise ValueError("artifact_age_seconds must not be negative")
        if artifact_age_seconds > max_age_seconds:
            return _unavailable(
                artifact_id,
                FailureReason.STALE,
                (
                    "Artifact exceeds the maximum permitted age: "
                    f"age_seconds={artifact_age_seconds}, "
                    f"max_age_seconds={max_age_seconds}."
                ),
            )

    if latency_ms is not None:
        if latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        if latency_ms > max_latency_ms:
            return _unavailable(
                artifact_id,
                FailureReason.SLOW,
                (
                    "Artifact/runtime response exceeded the latency budget: "
                    f"latency_ms={latency_ms}, "
                    f"max_latency_ms={max_latency_ms}."
                ),
            )

    return ArtifactHealth(
        artifact_id=artifact_id,
        status=ArtifactStatus.AVAILABLE,
        failure_reason=FailureReason.NONE,
        detail="Artifact passed all declared availability checks.",
        substitution_performed=False,
    )


def evaluate_runtime_artifact(
    *,
    artifact_id: str,
    path: Path,
    expected_sha256: str | None = None,
    expected_schema_version: str | None = None,
    actual_schema_version: str | None = None,
    artifact_age_seconds: float | None = None,
    latency_ms: float | None = None,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    max_latency_ms: float = DEFAULT_MAX_LATENCY_MS,
) -> dict[str, Any]:
    """Return the auditable runtime availability result.

    The returned contract deliberately contains no replacement artifact.
    """

    health = validate_artifact(
        artifact_id=artifact_id,
        path=path,
        expected_sha256=expected_sha256,
        expected_schema_version=expected_schema_version,
        actual_schema_version=actual_schema_version,
        artifact_age_seconds=artifact_age_seconds,
        latency_ms=latency_ms,
        max_age_seconds=max_age_seconds,
        max_latency_ms=max_latency_ms,
    )

    result = {
        "artifact_id": health.artifact_id,
        "status": health.status.value,
        "failure_reason": health.failure_reason.value,
        "detail": health.detail,
        "substitution_performed": health.substitution_performed,
        "human_approval_required": health.human_approval_required,
        "real_action_executed": health.real_action_executed,
    }

    if health.status is ArtifactStatus.UNAVAILABLE:
        result["decision"] = "unavailable"
    else:
        result["decision"] = "available"

    return result


def build_failure_matrix() -> list[dict[str, Any]]:
    """Return the declared RW-090-5 artifact failure behavior matrix."""

    return [
        {
            "failure": FailureReason.MISSING.value,
            "runtime_status": ArtifactStatus.UNAVAILABLE.value,
            "decision": "unavailable",
            "silent_substitution": False,
        },
        {
            "failure": FailureReason.CORRUPT.value,
            "runtime_status": ArtifactStatus.UNAVAILABLE.value,
            "decision": "unavailable",
            "silent_substitution": False,
        },
        {
            "failure": FailureReason.STALE.value,
            "runtime_status": ArtifactStatus.UNAVAILABLE.value,
            "decision": "unavailable",
            "silent_substitution": False,
        },
        {
            "failure": FailureReason.INCOMPATIBLE.value,
            "runtime_status": ArtifactStatus.UNAVAILABLE.value,
            "decision": "unavailable",
            "silent_substitution": False,
        },
        {
            "failure": FailureReason.SLOW.value,
            "runtime_status": ArtifactStatus.UNAVAILABLE.value,
            "decision": "unavailable",
            "silent_substitution": False,
        },
    ]


def write_report(path: Path) -> None:
    """Write the versioned RW-090-5 contract artifact."""

    payload = {
        "task": "RW-090-5",
        "artifact_type": "artifact_failure_matrix",
        "synthetic_only": True,
        "failure_matrix": build_failure_matrix(),
        "contract": {
            "missing_is_unavailable": True,
            "corrupt_is_unavailable": True,
            "stale_is_unavailable": True,
            "incompatible_is_unavailable": True,
            "slow_is_unavailable": True,
            "silent_substitution_forbidden": True,
            "replacement_artifact_not_selected": True,
            "human_approval_required": True,
            "real_action_executed": False,
            "physical_safety_determination": "not_determined",
            "operational_state_claimed": False,
        },
        "availability_policy": {
            "max_age_seconds": DEFAULT_MAX_AGE_SECONDS,
            "max_latency_ms": DEFAULT_MAX_LATENCY_MS,
            "checksum_algorithm": "sha256",
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    output = Path("artifacts/ransomware/offline/rw0905_artifact_failure_matrix.json")
    write_report(output)
    print(f"RW-090-5 wrote: {output}")
