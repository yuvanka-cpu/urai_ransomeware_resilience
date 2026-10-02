from pathlib import Path

from config.ransomware.rw0905_artifact_availability import (
    ArtifactStatus,
    FailureReason,
    build_failure_matrix,
    validate_artifact,
)


def test_rw0905_failure_matrix_contract():
    matrix = build_failure_matrix()

    assert len(matrix) == 5

    for entry in matrix:
        assert entry["runtime_status"] == "unavailable"
        assert entry["decision"] == "unavailable"
        assert entry["silent_substitution"] is False


def test_rw0905_missing_artifact_is_unavailable(tmp_path: Path):
    result = validate_artifact(
        artifact_id="missing",
        path=tmp_path / "missing.json",
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.failure_reason is FailureReason.MISSING
    assert result.substitution_performed is False


def test_rw0905_corrupt_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("bad", encoding="utf-8")

    result = validate_artifact(
        artifact_id="corrupt",
        path=artifact,
        expected_sha256="0" * 64,
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.failure_reason is FailureReason.CORRUPT
    assert result.substitution_performed is False


def test_rw0905_stale_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("ok", encoding="utf-8")

    result = validate_artifact(
        artifact_id="stale",
        path=artifact,
        artifact_age_seconds=101,
        max_age_seconds=100,
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.failure_reason is FailureReason.STALE
    assert result.substitution_performed is False


def test_rw0905_incompatible_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("ok", encoding="utf-8")

    result = validate_artifact(
        artifact_id="incompatible",
        path=artifact,
        expected_schema_version="2.0",
        actual_schema_version="1.0",
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.failure_reason is FailureReason.INCOMPATIBLE
    assert result.substitution_performed is False


def test_rw0905_slow_artifact_is_unavailable(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("ok", encoding="utf-8")

    result = validate_artifact(
        artifact_id="slow",
        path=artifact,
        latency_ms=101,
        max_latency_ms=100,
    )

    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.failure_reason is FailureReason.SLOW
    assert result.substitution_performed is False


def test_rw0905_healthy_artifact_is_available(tmp_path: Path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("ok", encoding="utf-8")

    result = validate_artifact(
        artifact_id="healthy",
        path=artifact,
        artifact_age_seconds=10,
        latency_ms=10,
    )

    assert result.status is ArtifactStatus.AVAILABLE
    assert result.failure_reason is FailureReason.NONE
    assert result.substitution_performed is False
