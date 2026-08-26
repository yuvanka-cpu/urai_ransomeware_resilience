from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_normal_mock():
    response = client.get("/mock/normal")

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "normal"
    assert data["human_approval_required"] is True
    assert data["real_action_executed"] is False


def test_investigate_mock():
    response = client.get("/mock/investigate")

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "investigate"
    assert data["human_approval_required"] is True
    assert data["real_action_executed"] is False


def test_high_risk_mock():
    response = client.get("/mock/high-risk")

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "high_risk"
    assert data["human_approval_required"] is True
    assert data["real_action_executed"] is False


def test_unavailable_mock():
    response = client.get("/mock/unavailable")

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "unavailable"
    assert data["data_provenance"] == "UNAVAILABLE"
    assert data["warnings"]
    assert data["human_approval_required"] is True
    assert data["real_action_executed"] is False


def test_fallback_mock():
    response = client.get("/mock/fallback")

    assert response.status_code == 200

    data = response.json()

    assert data["data_provenance"] == "FALLBACK"
    assert data["runtime_state"] == "fallback"
    assert data["warnings"]
    assert data["human_approval_required"] is True
    assert data["real_action_executed"] is False