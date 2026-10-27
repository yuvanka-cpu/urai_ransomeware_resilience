from __future__ import annotations

from fastapi.testclient import TestClient

from config.ransomware import rw1006_internal_api_cycle2 as api


client = TestClient(api.app)

VALID_REQUEST = {
    "schema_version": "1.0",
    "mode": "synthetic_scenario",
    "industry": "energy",
    "site_id": "cycle2-demo-site",
    "site_type": "substation",
    "scenario_id": "rw-attack-cycle2-test",
    "observable_input": {},
}


def test_rw1006_cycle2_health_contract():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "task": "RW-100-6",
        "schema_version": "1.0",
    }


def test_rw1006_cycle2_inference_response_envelope(monkeypatch):
    """Test response assembly without loading or scoring scenarios."""

    expected_result = {
        "task": "RW-100-3",
        "bundle_version": "rw0906_v2",
        "sector": "energy",
        "decision": "investigate",
        "runtime_contract": {
            "synthetic_only": True,
            "human_approval_required": True,
            "real_action_executed": False,
            "operational_state_claimed": False,
            "physical_safety_determination": "not_determined",
        },
    }

    monkeypatch.setattr(
        api,
        "_score_scenario",
        lambda request: expected_result,
    )

    response = client.post(
        "/internal/ransomware/infer",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["schema_version"] == "1.0"
    assert payload["task"] == "RW-100-6"
    assert payload["mode"] == "synthetic_scenario"
    assert payload["scenario_id"] == VALID_REQUEST["scenario_id"]
    assert payload["bundle_version"] == "rw0906_v2"
    assert payload["request_id"]
    assert payload["trace_id"]
    assert payload["result"] == expected_result
    assert payload["runtime_contract"] == expected_result["runtime_contract"]


def test_rw1006_cycle2_rejects_nested_ground_truth():
    request = {
        **VALID_REQUEST,
        "observable_input": {
            "nested": {
                "ground_truth": {
                    "is_ransomware": True,
                }
            }
        },
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_cycle2_rejects_cross_sector_site():
    request = {
        **VALID_REQUEST,
        "industry": "petrochemical",
        "site_type": "substation",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_cycle2_rejects_extra_request_fields():
    request = {
        **VALID_REQUEST,
        "decision": "high_risk",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_cycle2_rejects_blank_site_id():
    request = {
        **VALID_REQUEST,
        "site_id": "   ",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_cycle2_rejects_blank_scenario_id():
    request = {
        **VALID_REQUEST,
        "scenario_id": "   ",
    }

    response = client.post(
        "/internal/ransomware/infer",
        json=request,
    )

    assert response.status_code == 422


def test_rw1006_cycle2_observable_timeline_safety_contract(monkeypatch):
    """Timeline endpoint exposes synthetic evidence, not operational truth."""
    from config.ransomware.scenarios.scenario_event_assembler import (
        ObservableScenarioEvent,
    )
    from config.ransomware.scenarios.scenario_registry import FrozenScenario

    scenario = FrozenScenario(
        scenario_id="rw-cycle2-timeline-test",
        scenario_seed=42,
        use_case_id="test-use-case",
        industry="energy",
        scenario_family="test",
        site_types=("substation",),
        principal_assets=("asset-01",),
        observable_evidence=("authentication_login",),
        protected_boundary_context=("test-boundary",),
        variant="test",
        asset_id="asset-01",
        protected_boundary="test-boundary",
        split="train",
    )

    event = ObservableScenarioEvent(
        scenario_id=scenario.scenario_id,
        scenario_seed=42,
        split="train",
        sequence_index=0,
        event_time="2026-01-01T06:00:00Z",
        event_family="authentication",
        event_type="login_observation",
        asset_id="asset-01",
        attributes={"observable_value": 0.4},
    )

    monkeypatch.setattr(
        api,
        "_runtime_context",
        lambda: ({scenario.scenario_id: scenario}, None, None),
    )
    monkeypatch.setattr(
        api,
        "assemble_scenario_events",
        lambda _scenario: [event],
    )

    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "scenario_id": scenario.scenario_id,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["schema_version"] == "1.0"
    assert payload["task_id"] == "RW-120-6"
    assert payload["scenario_id"] == scenario.scenario_id
    assert payload["data_provenance"] == "synthetic_development"
    assert payload["is_operational_incident_timeline"] is False
    assert payload["status"] == "available"
    assert payload["event_count"] == 1
    assert payload["observed_asset_ids"] == ["asset-01"]
    assert payload["scope"] == "offline_synthetic_observable_evidence"
    assert "limitations" in payload


def test_rw1006_cycle2_observable_timeline_rejects_unknown_scenario(
    monkeypatch,
):
    monkeypatch.setattr(api, "_runtime_context", lambda: ({}, None, None))

    response = client.post(
        "/internal/ransomware/observable-timeline",
        json=VALID_REQUEST,
    )

    assert response.status_code == 404


def test_rw1006_cycle2_observable_timeline_rejects_cross_sector_site(
    monkeypatch,
):
    from config.ransomware.scenarios.scenario_registry import FrozenScenario

    scenario = FrozenScenario(
        scenario_id=VALID_REQUEST["scenario_id"],
        scenario_seed=42,
        use_case_id="test-use-case",
        industry="energy",
        scenario_family="test",
        site_types=("substation",),
        principal_assets=("asset-01",),
        observable_evidence=("authentication_login",),
        protected_boundary_context=("test-boundary",),
        variant="test",
        asset_id="asset-01",
        protected_boundary="test-boundary",
        split="train",
    )

    monkeypatch.setattr(
        api,
        "_runtime_context",
        lambda: ({scenario.scenario_id: scenario}, None, None),
    )

    response = client.post(
        "/internal/ransomware/observable-timeline",
        json={
            **VALID_REQUEST,
            "industry": "petrochemical",
            "site_type": "refinery",
        },
    )

    assert response.status_code == 422
