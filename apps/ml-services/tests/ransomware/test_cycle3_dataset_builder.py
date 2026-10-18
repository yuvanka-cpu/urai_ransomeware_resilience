"""Tests for Cycle 3 model-ready synthetic dataset construction."""

from collections import Counter, defaultdict
from dataclasses import FrozenInstanceError
from math import isfinite

import pytest

from config.ransomware.rw1002_feature_contract import (
    EXPECTED_FEATURE_COUNT,
    EXPECTED_FEATURES,
    validate_feature_row,
)
from config.ransomware.scenarios.cycle3_dataset_builder import (
    WINDOWS,
    build_cycle3_dataset,
)
from config.ransomware.shared.validation.feature_leakage_guard import (
    validate_deployed_features,
)


@pytest.fixture(scope="module")
def dataset():
    return build_cycle3_dataset()


def test_total_rows(dataset):
    assert len(dataset.rows) == 1260


def test_feature_count(dataset):
    assert len(dataset.feature_names) == EXPECTED_FEATURE_COUNT == 54


def test_exact_feature_contract(dataset):
    assert set(dataset.feature_names) == EXPECTED_FEATURES


def test_split_counts(dataset):
    counts = Counter(row.split for row in dataset.rows)

    assert counts == {
        "development": 900,
        "calibration": 360,
    }


def test_sector_split_counts(dataset):
    counts = Counter(
        (row.sector, row.split)
        for row in dataset.rows
    )

    assert counts == {
        ("energy", "development"): 420,
        ("energy", "calibration"): 180,
        ("petrochemical", "development"): 480,
        ("petrochemical", "calibration"): 180,
    }


def test_all_three_windows(dataset):
    assert {row.window_minutes for row in dataset.rows} == set(WINDOWS)


def test_every_scenario_has_three_windows(dataset):
    windows_by_scenario = defaultdict(set)

    for row in dataset.rows:
        windows_by_scenario[row.scenario_id].add(row.window_minutes)

    assert len(windows_by_scenario) == 420
    assert all(
        windows == set(WINDOWS)
        for windows in windows_by_scenario.values()
    )


def test_unique_scenario_window_pairs(dataset):
    identities = [
        (row.scenario_id, row.window_minutes)
        for row in dataset.rows
    ]

    assert len(identities) == len(set(identities))


def test_no_asset_overlap_between_splits(dataset):
    assets = defaultdict(set)

    for row in dataset.rows:
        assets[row.split].add(row.asset_id)

    assert assets["development"].isdisjoint(
        assets["calibration"]
    )


def test_all_feature_rows_valid(dataset):
    for row in dataset.rows:
        features = dict(row.features)

        validate_feature_row(features)
        validate_deployed_features(list(features))

        assert len(features) == 54
        assert tuple(sorted(features)) == dataset.feature_names


def test_all_features_finite_numeric(dataset):
    for row in dataset.rows:
        for _, value in row.features:
            assert type(value) in (int, float)
            assert isfinite(value)


def test_metadata_not_in_features(dataset):
    forbidden_metadata = {
        "scenario_id",
        "sector",
        "asset_id",
        "split",
        "use_case_id",
        "variant",
        "window_minutes",
        "window_end_time",
        "label",
        "ground_truth",
    }

    assert not forbidden_metadata.intersection(dataset.feature_names)


def test_all_variants_in_each_split(dataset):
    variants = defaultdict(set)

    for row in dataset.rows:
        variants[row.split].add(row.variant)

    expected = {"attack", "benign", "fault", "normal"}

    assert variants["development"] == expected
    assert variants["calibration"] == expected


def test_all_use_cases_in_each_split(dataset):
    use_cases = defaultdict(set)

    for row in dataset.rows:
        use_cases[row.split].add(row.use_case_id)

    assert len(use_cases["development"]) == 10
    assert len(use_cases["calibration"]) == 10


def test_deterministic_dataset(dataset):
    assert dataset == build_cycle3_dataset()


def test_invalid_seed_rejected():
    for seed in (-1, True, 1.5, "123", None):
        with pytest.raises(ValueError):
            build_cycle3_dataset(seed=seed)


def test_dataset_immutable(dataset):
    with pytest.raises(FrozenInstanceError):
        dataset.seed = 123


def test_dataset_row_immutable(dataset):
    with pytest.raises(FrozenInstanceError):
        dataset.rows[0].split = "holdout"


def test_no_holdout_created(dataset):
    assert {row.split for row in dataset.rows} == {
        "development",
        "calibration",
    }
