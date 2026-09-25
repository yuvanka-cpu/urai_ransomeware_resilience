import json
from pathlib import Path

from app.schemas.supply_chain import SupplyChainUseCaseCatalogue


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "supply_chain"
    / "use_cases.json"
)


def load_supply_chain_catalogue():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_supply_chain_catalogue_validates():
    catalogue = SupplyChainUseCaseCatalogue.model_validate(
        load_supply_chain_catalogue()
    )

    assert catalogue.schema_version == "1.0"
    assert catalogue.domain == "supply_chain"
    assert len(catalogue.use_cases) == 1


def test_supply_chain_use_case_preserves_safety_boundary():
    catalogue = SupplyChainUseCaseCatalogue.model_validate(
        load_supply_chain_catalogue()
    )

    use_case = catalogue.use_cases[0]

    assert use_case.use_case_id == "SC-FW-SW-01"
    assert use_case.human_approval_required is True
    assert use_case.real_action_executed is False
    assert any("firmware flashing" in item.lower() for item in use_case.safety_boundaries)
    assert any("software package" in item.lower() for item in use_case.safety_boundaries)


def test_supply_chain_use_case_has_firmware_and_software_scope():
    catalogue = SupplyChainUseCaseCatalogue.model_validate(
        load_supply_chain_catalogue()
    )

    scope = set(catalogue.use_cases[0].attack_scope)

    assert "firmware artifact" in scope
    assert "software package" in scope
