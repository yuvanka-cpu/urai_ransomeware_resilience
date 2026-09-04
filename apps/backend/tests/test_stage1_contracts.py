import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.enums import (
    AssetState,
    Decision,
    IncidentStage,
    OperationalImpactStatus,
)
from app.schemas.responses import OperationalDependencyImpact
from app.schemas.stage1 import (
    AcceptanceGateFile,
    AssetStateDefinition,
    RecommendationTemplate,
    UseCaseCatalogue,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONFIG_ROOT = REPOSITORY_ROOT / "apps" / "ml-services" / "config" / "ransomware"


def load_json(relative_path: str):
    return json.loads((CONFIG_ROOT / relative_path).read_text(encoding="utf-8"))


def test_ten_unique_sector_use_cases_validate():
    energy = UseCaseCatalogue.model_validate(load_json("energy/use_cases.json"))
    petrochemical = UseCaseCatalogue.model_validate(
        load_json("petrochemical/use_cases.json")
    )

    all_use_cases = energy.use_cases + petrochemical.use_cases
    assert len(all_use_cases) == 10
    assert len({use_case.use_case_id for use_case in all_use_cases}) == 10
    assert {use_case.use_case_id for use_case in energy.use_cases} == {
        f"EN-RW-0{number}" for number in range(1, 6)
    }
    assert {use_case.use_case_id for use_case in petrochemical.use_cases} == {
        f"PC-RW-0{number}" for number in range(1, 6)
    }


def test_site_types_are_closed_and_sector_specific():
    contract = load_json("industry_site_types.json")
    assert contract["industries"] == ["energy", "petrochemical"]
    assert set(contract["site_types"]) == {
        "control_centre",
        "substation",
        "refinery",
        "petrochemical_complex",
    }
    assert set(contract["permitted_site_types_by_industry"]["energy"]) == {
        "control_centre",
        "substation",
    }
    assert set(contract["permitted_site_types_by_industry"]["petrochemical"]) == {
        "refinery",
        "petrochemical_complex",
    }


def test_asset_state_definitions_match_enum():
    definitions = [
        AssetStateDefinition.model_validate(item)
        for item in load_json("asset_states.json")["states"]
    ]
    assert {item.state for item in definitions} == {item.value for item in AssetState}
    assert len(definitions) == 5


def test_decision_and_operational_contract_preserves_safety_separation():
    contract = load_json("decision_operational_contract.json")
    assert contract["decisions"] == [item.value for item in Decision]
    assert contract["incident_stages"] == [item.value for item in IncidentStage]
    assert contract["operational_impact_statuses"] == [
        item.value for item in OperationalImpactStatus
    ]
    assert contract["invariants"] == {
        "incident_stage_is_cyber_only": True,
        "physical_safety_determination": "not_determined",
        "operational_state_claimed": False,
        "human_approval_required": True,
        "real_action_executed": False,
    }


def test_operational_dependency_cannot_claim_physical_state():
    valid = {
        "service_id": "historian_support",
        "impact_status": "potential_dependency_impact",
        "evidence": ["synthetic service-health evidence"],
        "limitations": ["physical process state is not observed"],
        "physical_safety_determination": "not_determined",
        "operational_state_claimed": False,
    }
    OperationalDependencyImpact.model_validate(valid)

    with pytest.raises(ValidationError):
        OperationalDependencyImpact.model_validate(
            {**valid, "operational_state_claimed": True}
        )
    with pytest.raises(ValidationError):
        OperationalDependencyImpact.model_validate(
            {**valid, "physical_safety_determination": "safe"}
        )


def test_recommendations_cover_all_use_cases_and_remain_review_only():
    raw_templates = load_json("recommendation_templates.json")["templates"]
    templates = [RecommendationTemplate.model_validate(item) for item in raw_templates]
    assert len(templates) == 10
    assert len({item.template_id for item in templates}) == 10
    assert {item.use_case_id for item in templates} == {
        *(f"EN-RW-0{number}" for number in range(1, 6)),
        *(f"PC-RW-0{number}" for number in range(1, 6)),
    }
    permitted_prompt_openers = {"review", "confirm", "consult", "request", "compare"}
    for template in templates:
        assert template.human_approval_required is True
        assert template.real_action_executed is False
        assert all(
            prompt.split(maxsplit=1)[0].lower() in permitted_prompt_openers
            for prompt in template.review_prompts
        )


def test_machine_readable_acceptance_gates_match_catalogues():
    gates = AcceptanceGateFile.model_validate(load_json("acceptance_gates.json"))
    catalogues = [
        UseCaseCatalogue.model_validate(load_json("energy/use_cases.json")),
        UseCaseCatalogue.model_validate(load_json("petrochemical/use_cases.json")),
    ]
    use_cases = {
        use_case.use_case_id: use_case
        for catalogue in catalogues
        for use_case in catalogue.use_cases
    }
    assert set(gates.use_cases) == set(use_cases)
    for use_case_id, metrics in gates.use_cases.items():
        assert {metric.metric_id for metric in metrics} == set(
            use_cases[use_case_id].acceptance_metric_ids
        )
        assert all(metric.sector_report_required for metric in metrics)


def test_acceptance_thresholds_match_approved_stage_one_contract():
    gates = AcceptanceGateFile.model_validate(load_json("acceptance_gates.json"))
    indexed = {
        metric.metric_id: (metric.operator, metric.value, metric.unit)
        for metrics in gates.use_cases.values()
        for metric in metrics
    }
    expected = {
        "EN-RW-01-M01": ("gte", 0.90, "ratio"),
        "EN-RW-01-M02": ("gte", 0.85, "ratio"),
        "EN-RW-01-M03": ("lte", 0.10, "ratio"),
        "EN-RW-02-M01": ("gte", 0.85, "ratio"),
        "EN-RW-02-M02": ("gte", 0.80, "ratio"),
        "EN-RW-02-M03": ("lte", 0.10, "ratio"),
        "EN-RW-03-M01": ("gte", 0.85, "ratio"),
        "EN-RW-03-M02": ("lte", 0.10, "ratio"),
        "EN-RW-04-M01": ("lte", 0.05, "ratio"),
        "EN-RW-04-M02": ("gte", 0.95, "ratio"),
        "EN-RW-05-M01": ("gte", 0.85, "ratio"),
        "EN-RW-05-M02": ("lte", 0.10, "ratio"),
        "PC-RW-01-M01": ("gte", 0.90, "ratio"),
        "PC-RW-01-M02": ("gte", 0.85, "ratio"),
        "PC-RW-01-M03": ("lte", 0.10, "ratio"),
        "PC-RW-02-M01": ("lte", 0.10, "ratio"),
        "PC-RW-02-M02": ("gte", 0.90, "ratio"),
        "PC-RW-03-M01": ("gte", 0.85, "ratio"),
        "PC-RW-03-M02": ("lte", 0.10, "ratio"),
        "PC-RW-04-M01": ("gte", 0.95, "ratio"),
        "PC-RW-04-M02": ("lte", 0.05, "ratio"),
        "PC-RW-05-M01": ("gte", 0.85, "ratio"),
        "PC-RW-05-M02": ("lte", 0.10, "ratio"),
    }
    for metric_id, threshold in expected.items():
        assert indexed[metric_id] == threshold
