"""Tests for RW-120-8 recovery evidence availability."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.responses import BackupReadiness
from app.services.ransomware_recovery_evidence import (
    REQUIRED_EVIDENCE,
    assess_recovery_evidence,
)


client = TestClient(app)
ENDPOINT = "/api/v1/ransomware/recovery/evidence"


def test_recovery_evidence_is_explicitly_unavailable():
    result = assess_recovery_evidence()

    assert result["task_id"] == "RW-120-8"
    assert result["status"] == "unavailable"
    assert result["data_provenance"] == "not_established"
    assert result["is_operational_recovery_verified"] is False


def test_all_six_recovery_requirements_are_reported():
    result = assess_recovery_evidence()

    assert len(result["checks"]) == 6
    assert set(result["checks"]) == set(REQUIRED_EVIDENCE)

    for check in result["checks"].values():
        assert check["status"] == "unavailable"
        assert check["verified_value"] is None
        assert check["evidence_required"]


def test_backup_readiness_contains_no_fabricated_values():
    result = assess_recovery_evidence()
    readiness = BackupReadiness.model_validate(result["backup_readiness"])

    assert readiness.latest_backup_age_hours is None
    assert readiness.immutable_copy_available is None
    assert readiness.last_restore_test_age_days is None
    assert readiness.configuration_coverage_percent is None
    assert readiness.limitations


def test_no_resilience_score_is_invented():
    result = assess_recovery_evidence()

    assert result["resilience_score"] is None


def test_human_approval_and_no_action_safety():
    result = assess_recovery_evidence()

    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False
    assert result["physical_safety_determination"] == "not_determined"


def test_recovery_evidence_endpoint_is_read_only_and_unavailable():
    response = client.get(ENDPOINT)

    assert response.status_code == 200

    data = response.json()

    assert data["task_id"] == "RW-120-8"
    assert data["status"] == "unavailable"
    assert data["is_operational_recovery_verified"] is False
    assert data["real_action_executed"] is False
    assert data["human_approval_required"] is True
    assert data["physical_safety_determination"] == "not_determined"