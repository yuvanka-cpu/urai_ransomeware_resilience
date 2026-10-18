"""Tests for Cycle 3 illustrative background measurements."""

from collections import Counter
from dataclasses import fields
import inspect

import pytest

from config.ransomware.scenarios.cycle3_background_measurements import (
    BACKGROUND_STREAM_NAMESPACE,
    Cycle3BackgroundMeasurement,
    _background_stream_seed,
    build_cycle3_background_measurements,
)
from config.ransomware.scenarios.cycle3_measurement_profile import (
    build_cycle3_measurement_profile,
)
from config.ransomware.scenarios.cycle3_measurement_seed import (
    build_cycle3_measurement_seed,
)
from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    evaluate_cycle3_measurement_value,
)


BASE_INPUTS = {
    "base_seed": 20261017,
    "sector": "energy",
    "asset_id": "energy-asset-01",
    "use_case_id": "EN-RW-01",
}


def build():
    return build_cycle3_background_measurements(**BASE_INPUTS)


def test_generator_returns_tuple():
    assert isinstance(build(), tuple)


def test_generator_returns_exactly_75_observations():
    assert len(build()) == 75


def test_generator_is_deterministic():
    assert build() == build()


def test_background_stream_namespace():
    assert BACKGROUND_STREAM_NAMESPACE == "urai-cycle3-background-v1"


def test_all_observations_have_expected_dataclass_type():
    assert all(
        isinstance(item, Cycle3BackgroundMeasurement)
        for item in build()
    )


def test_observation_schedule_matches_profile():
    profile = build_cycle3_measurement_profile()

    actual = tuple(
        (item.observation_minute, item.event_type)
        for item in build()
    )

    expected = tuple(
        (minute, event_type)
        for minute in profile.observation_minutes
        for event_type in profile.event_types
    )

    assert actual == expected


def test_each_evidence_type_appears_15_times():
    counts = Counter(item.event_type for item in build())

    assert len(counts) == 5
    assert set(counts.values()) == {15}


def test_each_minute_contains_five_evidence_types():
    counts = Counter(
        item.observation_minute
        for item in build()
    )

    assert len(counts) == 15
    assert set(counts.values()) == {5}


def test_no_duplicate_observation_keys():
    keys = [
        (item.observation_minute, item.event_type)
        for item in build()
    ]

    assert len(keys) == len(set(keys))


def test_all_measurements_pass_value_gate():
    for item in build():
        decision = evaluate_cycle3_measurement_value(
            item.event_type,
            item.measured_value,
        )

        assert decision.allowed
        assert decision.reason is None


@pytest.mark.parametrize(
    "event_type",
    (
        "privilege_change_activity",
        "service_state_observation",
    ),
)
def test_boolean_measurements_have_exact_bool_type(event_type):
    values = [
        item.measured_value
        for item in build()
        if item.event_type == event_type
    ]

    assert values
    assert all(type(value) is bool for value in values)


@pytest.mark.parametrize(
    "event_type",
    (
        "file_write_activity",
        "file_rename_activity",
    ),
)
def test_count_measurements_are_nonnegative_integers(event_type):
    values = [
        item.measured_value
        for item in build()
        if item.event_type == event_type
    ]

    assert values
    assert all(
        type(value) is int and value >= 0
        for value in values
    )


def test_telemetry_freshness_values_are_nonnegative():
    values = [
        item.measured_value
        for item in build()
        if item.event_type == "telemetry_freshness_observation"
    ]

    assert values
    assert all(
        type(value) in (int, float) and value >= 0
        for value in values
    )


def test_measurement_record_excludes_labels_and_split():
    names = {
        field.name
        for field in fields(Cycle3BackgroundMeasurement)
    }

    forbidden = {
        "variant",
        "split",
        "label",
        "attack_label",
        "scenario_id",
        "scenario_seed",
        "scenario_family",
        "lifecycle_stage",
        "stage",
        "is_attack",
    }

    assert names.isdisjoint(forbidden)


def test_generator_signature_excludes_variant_and_split():
    parameters = inspect.signature(
        build_cycle3_background_measurements
    ).parameters

    assert set(parameters) == {
        "base_seed",
        "sector",
        "asset_id",
        "use_case_id",
    }


def test_background_is_shared_across_variant_contexts():
    variants = ("attack", "benign", "fault", "normal")

    results = {
        variant: build_cycle3_background_measurements(
            **BASE_INPUTS
        )
        for variant in variants
    }

    assert len(set(results.values())) == 1


def test_measurement_dataclass_is_immutable():
    item = build()[0]

    with pytest.raises(AttributeError):
        item.measured_value = 999


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("base_seed", 20261018),
        ("sector", "petrochemical"),
        ("asset_id", "energy-asset-02"),
        ("use_case_id", "EN-RW-02"),
    ),
)
def test_identity_change_changes_background(field, replacement):
    modified = dict(BASE_INPUTS)
    modified[field] = replacement

    assert build_cycle3_background_measurements(
        **modified
    ) != build()


def test_stream_seed_is_deterministic():
    measurement_seed = build_cycle3_measurement_seed(
        **BASE_INPUTS
    )

    first = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=1,
        event_type="file_write_activity",
    )

    second = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=1,
        event_type="file_write_activity",
    )

    assert first == second


def test_stream_seeds_differ_by_minute():
    measurement_seed = build_cycle3_measurement_seed(
        **BASE_INPUTS
    )

    first = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=1,
        event_type="file_write_activity",
    )

    second = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=2,
        event_type="file_write_activity",
    )

    assert first != second


def test_stream_seeds_differ_by_event_type():
    measurement_seed = build_cycle3_measurement_seed(
        **BASE_INPUTS
    )

    first = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=1,
        event_type="file_write_activity",
    )

    second = _background_stream_seed(
        measurement_seed=measurement_seed,
        observation_minute=1,
        event_type="file_rename_activity",
    )

    assert first != second


def test_all_75_stream_seeds_are_unique():
    measurement_seed = build_cycle3_measurement_seed(
        **BASE_INPUTS
    )

    profile = build_cycle3_measurement_profile()

    seeds = {
        _background_stream_seed(
            measurement_seed=measurement_seed,
            observation_minute=minute,
            event_type=event_type,
        )
        for minute in profile.observation_minutes
        for event_type in profile.event_types
    }

    assert len(seeds) == 75


@pytest.mark.parametrize(
    "invalid_seed",
    (-1, True, 1.5, "20261017", None),
)
def test_invalid_base_seed_is_rejected(invalid_seed):
    modified = dict(BASE_INPUTS)
    modified["base_seed"] = invalid_seed

    with pytest.raises(ValueError):
        build_cycle3_background_measurements(
            **modified
        )


@pytest.mark.parametrize(
    "field",
    ("sector", "asset_id", "use_case_id"),
)
@pytest.mark.parametrize(
    "invalid_value",
    ("", "   ", None, 123, True),
)
def test_invalid_identity_is_rejected(field, invalid_value):
    modified = dict(BASE_INPUTS)
    modified[field] = invalid_value

    with pytest.raises(ValueError):
        build_cycle3_background_measurements(
            **modified
        )


def test_generator_does_not_modify_input_dictionary():
    inputs = dict(BASE_INPUTS)

    build_cycle3_background_measurements(**inputs)

    assert inputs == BASE_INPUTS


def test_generator_has_no_training_or_model_dependency():
    source = inspect.getsource(
        build_cycle3_background_measurements
    )

    forbidden = (
        "model.fit(",
        "predict_proba(",
        "train_test_split(",
        "final_holdout",
    )

    assert all(token not in source for token in forbidden)
