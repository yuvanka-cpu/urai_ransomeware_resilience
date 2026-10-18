"""Tests for the Cycle 3 scenario adapter."""

from collections import Counter, defaultdict
from dataclasses import FrozenInstanceError

import pytest

from config.ransomware.asset_compatibility_cycle3 import (
    validate_sector_asset,
)
from config.ransomware.scenarios.cycle3_scenario_adapter import (
    build_cycle3_adapted_scenarios,
)
from config.ransomware.scenarios.cycle3_split_assignment import (
    DEFAULT_SEED,
    SPLIT_VERSION,
    build_cycle3_split_manifest,
)
from config.ransomware.scenarios.scenario_registry import (
    FrozenScenario,
    _scenario_id,
    _scenario_seed,
)
from config.ransomware.scenarios.sector_compatible_cycle3 import (
    build_sector_compatible_scenarios,
)


@pytest.fixture(scope="module")
def batch():
    return build_cycle3_adapted_scenarios()


def test_total_scenarios(batch):
    assert len(batch.scenarios) == 420


def test_version_and_seed(batch):
    assert batch.version == SPLIT_VERSION
    assert batch.seed == DEFAULT_SEED


def test_existing_scenario_contract(batch):
    assert all(
        isinstance(scenario, FrozenScenario)
        for scenario in batch.scenarios
    )


def test_split_counts(batch):
    counts = Counter(scenario.split for scenario in batch.scenarios)

    assert counts == {
        "development": 300,
        "calibration": 120,
    }


def test_sector_split_counts(batch):
    counts = Counter(
        (scenario.industry, scenario.split)
        for scenario in batch.scenarios
    )

    assert counts == {
        ("energy", "development"): 140,
        ("energy", "calibration"): 60,
        ("petrochemical", "development"): 160,
        ("petrochemical", "calibration"): 60,
    }


def test_every_asset_sector_compatible(batch):
    for scenario in batch.scenarios:
        result = validate_sector_asset(
            scenario.industry,
            scenario.asset_id,
        )
        assert result.compatible


def test_no_asset_overlap(batch):
    assets = defaultdict(set)

    for scenario in batch.scenarios:
        assets[scenario.split].add(scenario.asset_id)

    assert assets["development"].isdisjoint(
        assets["calibration"]
    )


def test_all_scenario_ids_unique(batch):
    ids = [scenario.scenario_id for scenario in batch.scenarios]

    assert len(ids) == len(set(ids))


def test_scenarios_sorted_by_id(batch):
    ids = [scenario.scenario_id for scenario in batch.scenarios]

    assert ids == sorted(ids)


def test_all_variants_present_in_each_split(batch):
    variants = defaultdict(set)

    for scenario in batch.scenarios:
        variants[scenario.split].add(scenario.variant)

    expected = {"attack", "benign", "fault", "normal"}

    assert variants["development"] == expected
    assert variants["calibration"] == expected


def test_all_use_cases_present_in_each_split(batch):
    use_cases = defaultdict(set)

    for scenario in batch.scenarios:
        use_cases[scenario.split].add(scenario.use_case_id)

    assert len(use_cases["development"]) == 10
    assert len(use_cases["calibration"]) == 10


def test_exact_manifest_assignments(batch):
    manifest = build_cycle3_split_manifest()

    expected = Counter(
        (
            item.sector,
            item.asset_id,
            item.use_case_id,
            item.variant,
            item.split,
        )
        for item in manifest.assignments
    )

    actual = Counter(
        (
            scenario.industry,
            scenario.asset_id,
            scenario.use_case_id,
            scenario.variant,
            scenario.split,
        )
        for scenario in batch.scenarios
    )

    assert actual == expected


def test_deterministic_scenario_ids_and_seeds(batch):
    lookup = {}

    for sector in ("energy", "petrochemical"):
        source_batch = build_sector_compatible_scenarios(sector)

        for scenario in source_batch.scenarios:
            key = (
                scenario.industry,
                scenario.asset_id,
                scenario.use_case_id,
                scenario.variant,
            )
            seed = _scenario_seed(scenario, DEFAULT_SEED)
            lookup[key] = (_scenario_id(scenario, seed), seed)

    for scenario in batch.scenarios:
        key = (
            scenario.industry,
            scenario.asset_id,
            scenario.use_case_id,
            scenario.variant,
        )

        assert (
            scenario.scenario_id,
            scenario.scenario_seed,
        ) == lookup[key]


def test_repeated_builds_identical(batch):
    assert batch == build_cycle3_adapted_scenarios()


def test_no_holdout_assignments(batch):
    assert {scenario.split for scenario in batch.scenarios} == {
        "development",
        "calibration",
    }


def test_invalid_seeds_rejected():
    for seed in (-1, True, 1.5, "123", None):
        with pytest.raises(ValueError):
            build_cycle3_adapted_scenarios(seed=seed)


def test_batch_immutable(batch):
    with pytest.raises(FrozenInstanceError):
        batch.seed = 123


def test_scenario_immutable(batch):
    with pytest.raises(FrozenInstanceError):
        batch.scenarios[0].split = "holdout"
