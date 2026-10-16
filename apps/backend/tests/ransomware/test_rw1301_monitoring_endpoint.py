"""Tests for read-only offline data drift monitoring."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.routes import ransomware_monitoring as monitoring


client = TestClient(app)
ENDPOINT = "/api/v1/ransomware/monitoring/data-drift"


def test_valid_offline_report():
    response = client.get(ENDPOINT)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "drift_detected"
    assert data["data_provenance"] == "synthetic_development"
    assert data["is_live_monitoring"] is False
    assert data["reference_count"] == 54
    assert data["current_count"] == 54
    assert len(data["feature_psi"]) == 54


def test_missing_report_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(
        monitoring,
        "REPORT_PATH",
        tmp_path / "missing.json",
    )

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert response.json()["is_live_monitoring"] is False


def test_corrupted_report_is_unavailable(monkeypatch, tmp_path):
    path = tmp_path / "corrupted.json"
    path.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(monitoring, "REPORT_PATH", path)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_incompatible_report_is_unavailable(monkeypatch, tmp_path):
    path = tmp_path / "incompatible.json"
    path.write_text(
        json.dumps({
            "task_id": "RW-130-1",
            "status": "drift_detected",
            "is_live_monitoring": True,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(monitoring, "REPORT_PATH", path)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_inconsistent_drift_result_is_unavailable(monkeypatch, tmp_path):
    report = json.loads(
        monitoring.REPORT_PATH.read_text(encoding="utf-8")
    )
    report["drifted_features"] = []

    path = tmp_path / "inconsistent.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    monkeypatch.setattr(monitoring, "REPORT_PATH", path)

    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
