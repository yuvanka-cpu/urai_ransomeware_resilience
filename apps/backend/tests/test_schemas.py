import pytest
from pydantic import ValidationError

from app.schemas.requests import RansomwareRequest
from app.schemas.responses import RansomwareResponse
from app.schemas.enums import Decision, IncidentStage, Severity


def test_valid_request_schema():
    request = RansomwareRequest(
    schema_version="1.0",
    use_case="ransomware_resilience",
    industry="Energy",
    site_id="SITE-001",
    site_type="refinery",
    scenario_id="SCENARIO-001",
    observable_input={},
)

    assert request.industry == "Energy"
    assert request.site_id == "SITE-001"
    assert request.scenario_id == "SCENARIO-001"


def test_invalid_request_schema():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
        )


def test_valid_response_schema():
    response = RansomwareResponse(
        use_case="Energy & Petrochemical Ransomware Resilience",
        industry="Energy",
        site_id="SITE-001",
        site_type="refinery",
        scenario_id="SCENARIO-001",
        decision=Decision.NORMAL,
        incident_stage=IncidentStage.NONE,
        confidence=0.95,
        severity=Severity.LOW,
        resilience_score=90.0,
        affected_assets=[],
        suspected_assets=[],
        critical_services_at_risk=[],
        affected_zones=[],
        protected_boundaries=[],
        operational_dependency_impact=[],
        propagation_path=[],
        evidence_layers=[],
        triggered_rules=[],
        timeline=[],
        backup_readiness={},
        explanations=[],
        recommended_actions=[],
        human_approval_required=True,
        real_action_executed=False,
        artifact_provenance=[],
        data_provenance="SYNTHETIC_GROUND_TRUTH",
        warnings=[],
        request_id="REQ-001",
        trace_id="TRACE-001",
        runtime_state="mock",
    )

    assert response.decision == Decision.NORMAL
    assert response.human_approval_required is True
    assert response.real_action_executed is False


def test_real_action_executed_true_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareResponse(
            use_case="Energy & Petrochemical Ransomware Resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            decision=Decision.NORMAL,
            incident_stage=IncidentStage.NONE,
            confidence=0.95,
            severity=Severity.LOW,
            resilience_score=90.0,
            affected_assets=[],
            suspected_assets=[],
            critical_services_at_risk=[],
            affected_zones=[],
            protected_boundaries=[],
            operational_dependency_impact=[],
            propagation_path=[],
            evidence_layers=[],
            triggered_rules=[],
            timeline=[],
            backup_readiness={},
            explanations=[],
            recommended_actions=[],
            human_approval_required=True,
            real_action_executed=True,
            artifact_provenance=[],
            data_provenance="synthetic",
            warnings=[],
            request_id="REQ-001",
            runtime_state="mock",
        )


def test_human_approval_required_false_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareResponse(
            use_case="Energy & Petrochemical Ransomware Resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            decision=Decision.NORMAL,
            incident_stage=IncidentStage.NONE,
            confidence=0.95,
            severity=Severity.LOW,
            resilience_score=90.0,
            affected_assets=[],
            suspected_assets=[],
            critical_services_at_risk=[],
            affected_zones=[],
            protected_boundaries=[],
            operational_dependency_impact=[],
            propagation_path=[],
            evidence_layers=[],
            triggered_rules=[],
            timeline=[],
            backup_readiness={},
            explanations=[],
            recommended_actions=[],
            human_approval_required=False,
            real_action_executed=False,
            artifact_provenance=[],
            data_provenance="synthetic",
            warnings=[],
            request_id="REQ-001",
            runtime_state="mock",
        )
