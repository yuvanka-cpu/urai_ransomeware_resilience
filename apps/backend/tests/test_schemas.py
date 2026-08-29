import pytest
from pydantic import ValidationError

from app.schemas.requests import RansomwareRequest
from app.schemas.responses import RansomwareResponse
from app.schemas.enums import Decision, IncidentStage, Severity, DataProvenance


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
            data_provenance="SYNTHETIC_GROUND_TRUTH",
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
            data_provenance="SYNTHETIC_GROUND_TRUTH",
            warnings=[],
            request_id="REQ-001",
            runtime_state="mock",
        )
def test_all_controlled_provenance_values():
    expected = {
        "LIVE_MODEL",
        "SYNTHETIC_GROUND_TRUTH",
        "STATIC_SCENARIO_METADATA",
        "DERIVED_BY_BACKEND",
        "FALLBACK",
        "UNAVAILABLE",
    }

    actual = {value.value for value in DataProvenance}

    assert actual == expected
def test_invalid_industry_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="1.0",
            use_case="ransomware_resilience",
            industry="Finance",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            observable_input={},
        )


def test_invalid_site_type_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="1.0",
            use_case="ransomware_resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="unknown_site",
            scenario_id="SCENARIO-001",
            observable_input={},
        )


def test_invalid_schema_version_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="2.0",
            use_case="ransomware_resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            observable_input={},
        )


def test_empty_site_id_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="1.0",
            use_case="ransomware_resilience",
            industry="Energy",
            site_id="",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            observable_input={},
        )


def test_extra_request_field_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="1.0",
            use_case="ransomware_resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            observable_input={},
            unexpected_field="not_allowed",
        )


def test_ground_truth_in_observable_input_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareRequest(
            schema_version="1.0",
            use_case="ransomware_resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            observable_input={
                "ground_truth": "ransomware"
            },
        )


def test_confidence_above_one_is_rejected():
    with pytest.raises(ValidationError):
        RansomwareResponse(
            use_case="Energy & Petrochemical Ransomware Resilience",
            industry="Energy",
            site_id="SITE-001",
            site_type="refinery",
            scenario_id="SCENARIO-001",
            decision=Decision.NORMAL,
            incident_stage=IncidentStage.NONE,
            confidence=1.5,
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


def test_resilience_score_above_100_is_rejected():
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
            resilience_score=101.0,
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