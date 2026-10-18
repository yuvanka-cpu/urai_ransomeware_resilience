"""Tests for variant-independent Cycle 3 measurement seeds."""

import inspect

import pytest

from config.ransomware.scenarios.cycle3_measurement_seed import (
    MEASUREMENT_SEED_NAMESPACE,
    build_cycle3_measurement_seed,
)


BASE_INPUTS = {
    "base_seed": 20261017,
    "sector": "energy",
    "asset_id": "energy-asset-01",
    "use_case_id": "use-case-01",
}


def test_seed_is_deterministic():
    first = build_cycle3_measurement_seed(**BASE_INPUTS)
    second = build_cycle3_measurement_seed(**BASE_INPUTS)

    assert first == second


def test_seed_is_nonnegative_64_bit_integer():
    seed = build_cycle3_measurement_seed(**BASE_INPUTS)

    assert type(seed) is int
    assert 0 <= seed < 2**64


def test_seed_namespace_is_explicit():
    assert MEASUREMENT_SEED_NAMESPACE == "urai-cycle3-measurement-v1"


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("base_seed", 20261018),
        ("sector", "petrochemical"),
        ("asset_id", "energy-asset-02"),
        ("use_case_id", "use-case-02"),
    ),
)
def test_identity_changes_produce_different_seeds(field, replacement):
    modified = dict(BASE_INPUTS)
    modified[field] = replacement

    assert build_cycle3_measurement_seed(
        **modified
    ) != build_cycle3_measurement_seed(**BASE_INPUTS)


def test_seed_signature_excludes_variant_split_and_scenario_id():
    parameters = inspect.signature(
        build_cycle3_measurement_seed
    ).parameters

    assert set(parameters) == {
        "base_seed",
        "sector",
        "asset_id",
        "use_case_id",
    }

    assert "variant" not in parameters
    assert "split" not in parameters
    assert "scenario_id" not in parameters
    assert "scenario_seed" not in parameters


@pytest.mark.parametrize(
    "invalid_seed",
    (-1, True, False, 1.5, "20261017", None),
)
def test_invalid_base_seeds_are_rejected(invalid_seed):
    modified = dict(BASE_INPUTS)
    modified["base_seed"] = invalid_seed

    with pytest.raises(ValueError):
        build_cycle3_measurement_seed(**modified)


@pytest.mark.parametrize(
    "field",
    ("sector", "asset_id", "use_case_id"),
)
@pytest.mark.parametrize(
    "invalid_value",
    ("", "   ", None, 123, True),
)
def test_invalid_identity_values_are_rejected(field, invalid_value):
    modified = dict(BASE_INPUTS)
    modified[field] = invalid_value

    with pytest.raises(ValueError):
        build_cycle3_measurement_seed(**modified)


def test_field_boundaries_are_unambiguous():
    first = build_cycle3_measurement_seed(
        base_seed=1,
        sector="ab",
        asset_id="c",
        use_case_id="d",
    )

    second = build_cycle3_measurement_seed(
        base_seed=1,
        sector="a",
        asset_id="bc",
        use_case_id="d",
    )

    assert first != second


def test_seed_does_not_use_python_process_hash():
    source = inspect.getsource(build_cycle3_measurement_seed)

    assert "hashlib.sha256" in source
    assert "hash(" not in source


def test_seed_function_has_no_random_state_dependency():
    source = inspect.getsource(build_cycle3_measurement_seed)

    assert "random.seed" not in source
    assert "random.Random" not in source


def test_seed_does_not_modify_input_dictionary():
    inputs = dict(BASE_INPUTS)

    build_cycle3_measurement_seed(**inputs)

    assert inputs == BASE_INPUTS


def test_distinct_asset_use_case_pairs_have_distinct_sample_seeds():
    seeds = {
        build_cycle3_measurement_seed(
            base_seed=20261017,
            sector="energy",
            asset_id=f"asset-{asset_index}",
            use_case_id=f"use-case-{case_index}",
        )
        for asset_index in range(5)
        for case_index in range(5)
    }

    assert len(seeds) == 25
