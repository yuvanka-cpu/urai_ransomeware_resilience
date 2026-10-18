"""Tests for the Cycle 3 measurement-quality gate."""

from dataclasses import FrozenInstanceError

import pytest

from config.ransomware.scenarios.cycle3_measurement_audit import (
    Cycle3MeasurementAudit,
)
from config.ransomware.scenarios.cycle3_measurement_quality_gate import (
    Cycle3MeasurementQualityResult,
    evaluate_cycle3_measurement_quality,
)


def make_audit(
    *,
    total=10,
    measured=10,
    missing=0,
    nonfinite=0,
    mixed=False,
):
    """Construct a consistent synthetic audit summary."""

    assert total == measured + missing + nonfinite

    return Cycle3MeasurementAudit(
        event_count=total,
        measured_event_count=measured,
        missing_event_count=missing,
        source_counts=(),
        mixed_sources=mixed,
        nonfinite_value_count=nonfinite,
    )


def test_returns_quality_result():
    result = evaluate_cycle3_measurement_quality(make_audit())
    assert isinstance(result, Cycle3MeasurementQualityResult)


def test_complete_numeric_coverage_passes():
    result = evaluate_cycle3_measurement_quality(make_audit())
    assert result.passed is True
    assert result.missing_fraction == 0.0
    assert result.reasons == ()


def test_empty_window_fails():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=0, measured=0)
    )
    assert result.passed is False
    assert "empty_event_window" in result.reasons


def test_empty_window_missing_fraction_is_one():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=0, measured=0)
    )
    assert result.missing_fraction == 1.0


def test_missing_values_fail_by_default():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=9, missing=1)
    )
    assert result.passed is False
    assert "missing_numerical_values" in result.reasons


def test_missing_fraction_calculated_correctly():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=7, missing=3)
    )
    assert result.missing_fraction == pytest.approx(0.3)


def test_missing_fraction_at_threshold_passes():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=8, missing=2),
        max_missing_fraction=0.2,
    )
    assert result.passed is True


def test_missing_fraction_above_threshold_fails():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=7, missing=3),
        max_missing_fraction=0.2,
    )
    assert result.passed is False


def test_all_missing_fails_by_default():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=0, missing=10)
    )
    assert result.passed is False
    assert result.missing_fraction == 1.0


def test_all_missing_allowed_by_explicit_threshold():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=0, missing=10),
        max_missing_fraction=1.0,
    )
    assert result.passed is True


def test_nonfinite_values_fail():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=9, nonfinite=1)
    )
    assert result.passed is False
    assert "nonfinite_numerical_values" in result.reasons


def test_nonfinite_values_fail_even_with_relaxed_missingness():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=5, missing=4, nonfinite=1),
        max_missing_fraction=1.0,
    )
    assert result.passed is False
    assert "nonfinite_numerical_values" in result.reasons


def test_mixed_sources_fail_by_default():
    result = evaluate_cycle3_measurement_quality(
        make_audit(mixed=True)
    )
    assert result.passed is False
    assert "mixed_numerical_sources" in result.reasons


def test_mixed_sources_allowed_explicitly():
    result = evaluate_cycle3_measurement_quality(
        make_audit(mixed=True),
        allow_mixed_sources=True,
    )
    assert result.passed is True


def test_multiple_failure_reasons():
    result = evaluate_cycle3_measurement_quality(
        make_audit(
            total=10,
            measured=5,
            missing=4,
            nonfinite=1,
            mixed=True,
        )
    )
    assert result.reasons == (
        "nonfinite_numerical_values",
        "missing_numerical_values",
        "mixed_numerical_sources",
    )


@pytest.mark.parametrize(
    "threshold",
    [-0.1, 1.1, -1.0, 2.0],
)
def test_invalid_missing_threshold_rejected(threshold):
    with pytest.raises(ValueError, match="between 0 and 1"):
        evaluate_cycle3_measurement_quality(
            make_audit(),
            max_missing_fraction=threshold,
        )


def test_zero_threshold_is_valid():
    result = evaluate_cycle3_measurement_quality(
        make_audit(),
        max_missing_fraction=0.0,
    )
    assert result.passed is True


def test_one_threshold_is_valid():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=10, measured=0, missing=10),
        max_missing_fraction=1.0,
    )
    assert result.passed is True


def test_empty_window_fails_even_with_maximum_threshold():
    result = evaluate_cycle3_measurement_quality(
        make_audit(total=0, measured=0),
        max_missing_fraction=1.0,
    )
    assert result.passed is False
    assert result.reasons == ("empty_event_window",)


def test_quality_result_is_immutable():
    result = evaluate_cycle3_measurement_quality(make_audit())

    with pytest.raises(FrozenInstanceError):
        result.passed = False


def test_deterministic_result():
    audit = make_audit(total=10, measured=7, missing=3)

    first = evaluate_cycle3_measurement_quality(audit)
    second = evaluate_cycle3_measurement_quality(audit)

    assert first == second


def test_input_audit_unchanged():
    audit = make_audit(total=10, measured=8, missing=2)
    original = audit

    evaluate_cycle3_measurement_quality(audit)

    assert audit == original
