from config.ransomware.scenarios.scenario_registry import (
    SPLITS,
    build_frozen_scenarios,
    build_split_assignment_manifest,
)


ASSETS = [
    "energy-blr01-asset-identity-001",
    "energy-blr01-asset-engineering-001",
]


def test_scenario_identity_is_deterministic():
    first = build_frozen_scenarios(ASSETS, base_seed=20260921)
    second = build_frozen_scenarios(ASSETS, base_seed=20260921)

    assert first == second


def test_different_base_seed_changes_scenario_identity():
    first = build_frozen_scenarios(ASSETS, base_seed=20260921)
    second = build_frozen_scenarios(ASSETS, base_seed=20260922)

    assert first != second


def test_scenario_ids_are_unique():
    scenarios = build_frozen_scenarios(ASSETS)

    scenario_ids = [scenario.scenario_id for scenario in scenarios]

    assert len(scenario_ids) == len(set(scenario_ids))


def test_every_scenario_has_one_required_split():
    scenarios = build_frozen_scenarios(ASSETS)

    assert scenarios
    assert all(scenario.split in SPLITS for scenario in scenarios)


def test_all_required_splits_are_represented():
    scenarios = build_frozen_scenarios(ASSETS)

    observed_splits = {scenario.split for scenario in scenarios}

    assert observed_splits == set(SPLITS)


def test_scenario_seed_is_present_and_deterministic():
    first = build_frozen_scenarios(ASSETS)
    second = build_frozen_scenarios(ASSETS)

    assert all(isinstance(scenario.scenario_seed, int) for scenario in first)
    assert [s.scenario_seed for s in first] == [
        s.scenario_seed for s in second
    ]


def test_manifest_is_reproducible():
    first = build_split_assignment_manifest(ASSETS)
    second = build_split_assignment_manifest(ASSETS)

    assert first == second


def test_manifest_contains_required_split_assignment_fields():
    manifest = build_split_assignment_manifest(ASSETS)

    assert manifest["manifest_type"] == "split_assignment"
    assert manifest["scenario_count"] == len(manifest["assignments"])

    required = {
        "scenario_id",
        "scenario_seed",
        "use_case_id",
        "industry",
        "variant",
        "asset_id",
        "protected_boundary",
        "split",
    }

    for assignment in manifest["assignments"]:
        assert required.issubset(assignment)