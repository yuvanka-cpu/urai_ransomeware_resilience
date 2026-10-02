from pathlib import Path

import pytest

from config.ransomware.rw1005_unavailable_contract import (
    build_unavailable_result,
    validate_required_artifact,
)


@pytest.mark.parametrize(
    ("failure_reason", "detail"),
    [
        ("missing", "required artifact is missing"),
        ("corrupt", "required artifact is corrupt"),
        ("stale", "required artifact is stale"),
        ("incompatible", "required artifact is incompatible"),
        ("slow", "required artifact is slow"),
    ],
)
def test_all_required_failures_produce_unavailable(
    failure_reason: str,
    detail: str,
):
    result = build_unavailable_result(
        artifact_id="test-artifact",
        failure_reason=failure_reason,
        detail=detail,
    )

    assert result["decision"] == "unavailable"
    assert result["artifact_status"] == "unavailable"
    assert result["confidence"] is None
    assert result["severity"] == "low"
    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False
    assert result["operational_state_claimed"] is False
    assert result["physical_safety_determination"] == "not_determined"
    assert result["silent_substitution"] is False
    assert result["replacement_artifact_not_selected"] is True
    assert result["artifact_provenance"][0]["failure_reason"] == failure_reason


def test_missing_artifact_is_unavailable(tmp_path: Path):
    result = validate_required_artifact(
        artifact_id="missing-model",
        path=tmp_path / "does-not-exist.json",
    )

    assert result["decision"] == "unavailable"
    assert result["artifact_provenance"][0]["failure_reason"] == "missing"


def test_stale_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "model.json"
    artifact.write_text("synthetic", encoding="utf-8")

    result = validate_required_artifact(
        artifact_id="stale-model",
        path=artifact,
        artifact_age_seconds=24 * 60 * 60 + 1,
    )

    assert result["decision"] == "unavailable"
    assert result["artifact_provenance"][0]["failure_reason"] == "stale"


def test_slow_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "model.json"
    artifact.write_text("synthetic", encoding="utf-8")

    result = validate_required_artifact(
        artifact_id="slow-model",
        path=artifact,
        latency_ms=1001,
    )

    assert result["decision"] == "unavailable"
    assert result["artifact_provenance"][0]["failure_reason"] == "slow"


def test_unavailable_rejects_unknown_failure_reason():
    with pytest.raises(ValueError):
        build_unavailable_result(
            artifact_id="test-artifact",
            failure_reason="unknown",
            detail="invalid failure",
        )
