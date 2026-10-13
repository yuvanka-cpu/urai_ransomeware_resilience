"""Tests for RW-130-1 offline data drift monitoring."""

import pytest

from config.ransomware.rw1002_feature_contract import EXPECTED_FEATURES
from config.ransomware.rw1301_data_drift import (
    monitor_data_drift,
    population_stability_index,
)


def make_rows(count=60, shift=0.0):
    return [
        {
            feature: float((index % 20) + shift)
            for feature in EXPECTED_FEATURES
        }
        for index in range(count)
    ]


def test_identical_distributions_have_no_drift():
    rows = make_rows()
    result = monitor_data_drift(rows, rows)

    assert result["status"] == "no_drift_detected"
    assert result["drifted_features"] == []
    assert len(result["feature_psi"]) == 54


def test_shifted_distributions_detect_drift():
    reference = make_rows()
    current = make_rows(shift=100)

    result = monitor_data_drift(reference, current)

    assert result["status"] == "drift_detected"
    assert len(result["drifted_features"]) == 54


def test_insufficient_samples_are_unavailable():
    result = monitor_data_drift(make_rows(10), make_rows(10))

    assert result["status"] == "unavailable"
    assert result["feature_psi"] == {}


def test_invalid_feature_schema_is_unavailable():
    reference = make_rows()
    current = make_rows()

    for row in current:
        row.pop(next(iter(EXPECTED_FEATURES)))

    result = monitor_data_drift(reference, current)

    assert result["status"] == "unavailable"


def test_constant_reference_with_changed_values_detects_drift():
    reference = [
        {feature: 1.0 for feature in EXPECTED_FEATURES}
        for _ in range(60)
    ]

    result = monitor_data_drift(reference, make_rows())

    assert result["status"] == "drift_detected"
    assert len(result["drifted_features"]) == 54


def test_invalid_numeric_values_are_rejected():
    with pytest.raises(ValueError):
        population_stability_index(
            [float("nan")] * 60,
            [1.0] * 60,
        )


def test_constant_reference_and_identical_current_have_zero_psi():
    reference = [5.0] * 60
    current = [5.0] * 60

    assert population_stability_index(reference, current) == 0.0


def test_constant_reference_and_shifted_current_detect_drift():
    reference = [5.0] * 60
    current = [8.0] * 60

    assert population_stability_index(reference, current) >= 0.2


def test_constant_reference_with_partial_shift_detects_drift():
    reference = [5.0] * 60
    current = [5.0] * 30 + [8.0] * 30

    assert population_stability_index(reference, current) >= 0.2


def test_constant_reference_monitor_handles_unchanged_features():
    rows = [
        {feature: 1.0 for feature in EXPECTED_FEATURES}
        for _ in range(60)
    ]

    result = monitor_data_drift(rows, rows)

    assert result["status"] == "no_drift_detected"
    assert len(result["feature_psi"]) == 54
