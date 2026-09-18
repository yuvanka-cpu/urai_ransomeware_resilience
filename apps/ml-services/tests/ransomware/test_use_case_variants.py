from config.ransomware.scenarios.use_case_catalogue import ALL_USE_CASES
from config.ransomware.scenarios.use_case_variants import (
    generate_use_case_scenarios,
)


def test_generates_four_variants_for_every_use_case():
    scenarios = generate_use_case_scenarios(
        "energy-blr01-asset-engineering-001"
    )

    assert len(scenarios) == len(ALL_USE_CASES) * 4


def test_every_use_case_has_all_variants():
    scenarios = generate_use_case_scenarios(
        "energy-blr01-asset-engineering-001"
    )

    for use_case in ALL_USE_CASES:
        variants = {
            scenario.variant
            for scenario in scenarios
            if scenario.use_case_id == use_case.use_case_id
        }

        assert variants == {"normal", "attack", "benign", "fault"}


def test_sector_boundaries_are_present():
    scenarios = generate_use_case_scenarios(
        "petrochemical-mng01-asset-engineering-001"
    )

    assert all(scenario.protected_boundary for scenario in scenarios)


def test_scenarios_preserve_asset_identity():
    asset_id = "energy-blr01-asset-engineering-001"

    scenarios = generate_use_case_scenarios(asset_id)

    assert all(scenario.asset_id == asset_id for scenario in scenarios)
