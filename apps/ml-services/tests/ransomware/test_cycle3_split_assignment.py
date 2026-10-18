"""Tests for Cycle 3 deterministic asset-grouped development/calibration splits."""

from collections import Counter, defaultdict
from dataclasses import FrozenInstanceError

import pytest

from config.ransomware.scenarios.cycle3_split_assignment import (
    DEFAULT_SEED,
    SPLIT_VERSION,
    build_cycle3_split_manifest,
)


def test_total_scenario_count():
    manifest = build_cycle3_split_manifest()
    assert len(manifest.assignments) == 420


def test_split_counts():
    manifest = build_cycle3_split_manifest()
    counts = Counter(item.split for item in manifest.assignments)

    assert counts == {
        "development": 300,
        "calibration": 120,
    }


def test_sector_split_counts():
    manifest = build_cycle3_split_manifest()

    counts = Counter(
        (item.sector, item.split)
        for item in manifest.assignments
    )

    assert counts == {
        ("energy", "development"): 140,
        ("energy", "calibration"): 60,
        ("petrochemical", "development"): 160,
        ("petrochemical", "calibration"): 60,
    }


def test_zero_asset_overlap():
    manifest = build_cycle3_split_manifest()
    assets = defaultdict(set)

    for item in manifest.assignments:
        assets[item.split].add(item.asset_id)

    assert assets["development"].isdisjoint(assets["calibration"])


def test_every_asset_has_single_split():
    manifest = build_cycle3_split_manifest()
    asset_splits = defaultdict(set)

    for item in manifest.assignments:
        asset_splits[(item.sector, item.asset_id)].add(item.split)

    assert len(asset_splits) == 21
    assert all(len(splits) == 1 for splits in asset_splits.values())


def test_both_sectors_present_in_each_split():
    manifest = build_cycle3_split_manifest()
    sectors = defaultdict(set)

    for item in manifest.assignments:
        sectors[item.split].add(item.sector)

    assert sectors["development"] == {"energy", "petrochemical"}
    assert sectors["calibration"] == {"energy", "petrochemical"}


def test_all_variants_present_in_each_split():
    manifest = build_cycle3_split_manifest()
    variants = defaultdict(set)

    for item in manifest.assignments:
        variants[item.split].add(item.variant)

    expected = {"normal", "attack", "benign", "fault"}

    assert variants["development"] == expected
    assert variants["calibration"] == expected


def test_all_use_cases_present_in_each_split():
    manifest = build_cycle3_split_manifest()
    use_cases = defaultdict(set)

    for item in manifest.assignments:
        use_cases[item.split].add(item.use_case_id)

    assert len(use_cases["development"]) == 10
    assert len(use_cases["calibration"]) == 10


def test_no_holdout_created():
    manifest = build_cycle3_split_manifest()

    assert {item.split for item in manifest.assignments} == {
        "development",
        "calibration",
    }


def test_deterministic_assignments():
    first = build_cycle3_split_manifest()
    second = build_cycle3_split_manifest()

    assert first == second
    assert first.seed == DEFAULT_SEED
    assert first.version == SPLIT_VERSION


def test_invalid_seeds_rejected():
    for seed in (-1, True, 1.5, "123", None):
        with pytest.raises(ValueError):
            build_cycle3_split_manifest(seed=seed)


def test_manifest_is_immutable():
    manifest = build_cycle3_split_manifest()

    with pytest.raises(FrozenInstanceError):
        manifest.seed = 123


def test_assignment_is_immutable():
    manifest = build_cycle3_split_manifest()

    with pytest.raises(FrozenInstanceError):
        manifest.assignments[0].split = "holdout"
