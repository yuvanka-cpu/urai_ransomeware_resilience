from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.enums import DataProvenance, Decision, IncidentStage, Severity
from app.schemas.requests import RansomwareRequest
from app.schemas.responses import RansomwareResponse


def valid_request_data() -> dict:
    return {
        "schema_version": "1.0",
        "use_case": "ransomware_resilience",
        "industry": "energy",
        "site_id": "SITE-001",
        "site_type": "control_centre",
        "scenario_id": "SCENARIO-001",
        "observable_input": {"authentication_event_count": 3},
    }


def valid_response_data() -> dict:
    return {
        "use_case": "ransomware_resilience",
        "industry": "energy",
        "site_id": "SITE-001",
        "site_type": "control_centre",
        "scenario_id": "SCENARIO-001",
        "decision": Decision.NORMAL,
        "incident_stage": IncidentStage.NONE,
        "confidence": 0.95,
        "severity": Severity.LOW,
        "resilience_score": 90.0,
        "affected_assets": [],
        "suspected_assets": [],
        "potentially_exposed_assets": [],
        "protected_assets": [],
        "unknown_assets": [],
        "critical_services_at_risk": [],
        "affected_zones": [],
        "protected_boundaries": [],
        "operational_dependency_impact": [],
        "propagation_path": [],
        "evidence_layers": [],
        "triggered_rules": [],
        "timeline": [],
        "backup_readiness": {},
        "explanations": [],
        "recommended_actions": [],
        "human_approval_required": True,
        "real_action_executed": False,
        "artifact_provenance": [],
        "data_provenance": "SYNTHETIC_GROUND_TRUTH",
        "warnings": [],
        "request_id": "REQ-001",
        "trace_id": "TRACE-001",
        "runtime_state": "mocked",
    }


def error_locations(exc_info: pytest.ExceptionInfo[ValidationError]) -> set[tuple]:
    return {tuple(error["loc"]) for error in exc_info.value.errors()}


def test_valid_request_schema():
    request = RansomwareRequest(**valid_request_data())

    assert request.industry.value == "energy"
    assert request.site_id == "SITE-001"
    assert request.scenario_id == "SCENARIO-001"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("schema_version", "2.0"),
        ("use_case", "other"),
        ("industry", "Finance"),
        ("industry", "Energy"),
        ("site_type", "unknown_site"),
        ("site_id", ""),
        ("site_id", "   "),
        ("scenario_id", ""),
        ("scenario_id", "   "),
    ],
)
def test_invalid_request_contract_value_is_rejected(field, invalid_value):
    data = valid_request_data()
    data[field] = invalid_value

    with pytest.raises(ValidationError) as exc_info:
        RansomwareRequest(**data)

    assert (field,) in error_locations(exc_info)


def test_extra_request_field_is_rejected():
    data = valid_request_data()
    data["unexpected_field"] = "not_allowed"

    with pytest.raises(ValidationError) as exc_info:
        RansomwareRequest(**data)

    assert ("unexpected_field",) in error_locations(exc_info)


@pytest.mark.parametrize(
    ("industry", "site_type"),
    [("energy", "refinery"), ("petrochemical", "substation")],
)
def test_cross_sector_request_site_type_is_rejected(industry, site_type):
    data = valid_request_data()
    data.update({"industry": industry, "site_type": site_type})

    with pytest.raises(ValidationError):
        RansomwareRequest(**data)


@pytest.mark.parametrize(
    "observable_input",
    [
        {"ground_truth": "ransomware"},
        {"events": [{"ground_truth": "ransomware"}]},
        {"nested": {"synthetic_truth": {"affected": True}}},
        {"events": [{"truth_label": 1}]},
    ],
)
def test_reserved_truth_fields_are_rejected_at_any_depth(observable_input):
    data = valid_request_data()
    data["observable_input"] = observable_input

    with pytest.raises(ValidationError) as exc_info:
        RansomwareRequest(**data)

    assert ("observable_input",) in error_locations(exc_info)


def test_valid_response_schema():
    response = RansomwareResponse(**valid_response_data())

    assert response.decision == Decision.NORMAL
    assert response.human_approval_required is True
    assert response.real_action_executed is False


def test_real_action_executed_true_is_rejected_for_exact_field():
    data = valid_response_data()
    data["real_action_executed"] = True

    with pytest.raises(ValidationError) as exc_info:
        RansomwareResponse(**data)

    assert error_locations(exc_info) == {("real_action_executed",)}


def test_human_approval_required_false_is_rejected_for_exact_field():
    data = valid_response_data()
    data["human_approval_required"] = False

    with pytest.raises(ValidationError) as exc_info:
        RansomwareResponse(**data)

    assert error_locations(exc_info) == {("human_approval_required",)}


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("confidence", -0.01),
        ("confidence", 1.01),
        ("resilience_score", -0.01),
        ("resilience_score", 100.01),
        ("runtime_state", "arbitrary"),
        ("industry", "Energy"),
        ("site_type", "unknown_site"),
        ("request_id", "   "),
        ("trace_id", ""),
    ],
)
def test_invalid_response_contract_value_is_rejected(field, invalid_value):
    data = valid_response_data()
    data[field] = invalid_value

    with pytest.raises(ValidationError) as exc_info:
        RansomwareResponse(**data)

    assert (field,) in error_locations(exc_info)


def test_invalid_nested_backup_field_is_rejected():
    data = valid_response_data()
    data["backup_readiness"] = {"latest_backup_age_hours": -1}

    with pytest.raises(ValidationError) as exc_info:
        RansomwareResponse(**data)

    assert ("backup_readiness", "latest_backup_age_hours") in error_locations(
        exc_info
    )


def test_cross_sector_response_site_type_is_rejected():
    data = valid_response_data()
    data.update({"industry": "energy", "site_type": "petrochemical_complex"})

    with pytest.raises(ValidationError):
        RansomwareResponse(**data)


def test_artifact_provenance_requires_valid_checksum():
    data = deepcopy(valid_response_data())
    data["artifact_provenance"] = [
        {
            "artifact_name": "fusion-model",
            "version": "1.0.0",
            "checksum_sha256": "not-a-sha256",
            "status": "loaded",
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        RansomwareResponse(**data)

    assert (
        "artifact_provenance",
        0,
        "checksum_sha256",
    ) in error_locations(exc_info)


def test_all_controlled_provenance_values():
    expected = {
        "LIVE_MODEL",
        "SYNTHETIC_GROUND_TRUTH",
        "STATIC_SCENARIO_METADATA",
        "DERIVED_BY_BACKEND",
        "FALLBACK",
        "UNAVAILABLE",
    }

    assert {value.value for value in DataProvenance} == expected
