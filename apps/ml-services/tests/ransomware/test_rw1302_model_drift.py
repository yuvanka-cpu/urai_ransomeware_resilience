"""Tests for RW-130-2 offline model performance monitoring."""

from copy import deepcopy

from config.ransomware.rw1302_model_drift import compare_model_performance


def report(period, **metrics):
    values = {
        "precision": 0.85,
        "recall": 0.80,
        "f1": 0.82,
        "brier": 0.12,
    }
    values.update(metrics)
    return {
        "model_id": "rw0906_v2",
        "population_id": "energy_petrochemical",
        "metric_definition_id": "binary_v1",
        "period_end": period,
        "sample_count": 100,
        "metrics": values,
    }


REFERENCE = "2026-09-01T00:00:00+00:00"
CURRENT = "2026-10-01T00:00:00+00:00"


def test_identical_performance():
    result = compare_model_performance(report(REFERENCE), report(CURRENT))
    assert result["status"] == "no_drift_detected"


def test_recall_deterioration():
    result = compare_model_performance(
        report(REFERENCE), report(CURRENT, recall=0.55)
    )
    assert result["status"] == "drift_detected"
    assert result["metric_changes"]["recall"]["degraded"]


def test_brier_deterioration():
    result = compare_model_performance(
        report(REFERENCE), report(CURRENT, brier=0.25)
    )
    assert result["status"] == "drift_detected"


def test_improvement_is_not_drift():
    result = compare_model_performance(
        report(REFERENCE), report(CURRENT, recall=0.95, brier=0.05)
    )
    assert result["status"] == "no_drift_detected"


def test_missing_metric_unavailable():
    current = report(CURRENT)
    del current["metrics"]["recall"]
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_different_model_unavailable():
    current = report(CURRENT)
    current["model_id"] = "different_model"
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_insufficient_samples_unavailable():
    current = report(CURRENT)
    current["sample_count"] = 5
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_reversed_periods_unavailable():
    assert compare_model_performance(
        report(CURRENT), report(REFERENCE)
    )["status"] == "unavailable"


def test_invalid_metric_unavailable():
    current = report(CURRENT, precision=float("nan"))
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_population_mismatch_unavailable():
    current = report(CURRENT)
    current["population_id"] = "different_population"
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_custom_threshold():
    result = compare_model_performance(
        report(REFERENCE),
        report(CURRENT, recall=0.74),
        thresholds={"recall": 0.05},
    )
    assert result["status"] == "drift_detected"


def test_invalid_threshold_unavailable():
    assert compare_model_performance(
        report(REFERENCE),
        report(CURRENT),
        thresholds={"recall": -0.1},
    )["status"] == "unavailable"


def test_naive_timestamp_unavailable():
    current = report(CURRENT)
    current["period_end"] = "2026-10-01T00:00:00"
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"


def test_boolean_metric_unavailable():
    current = report(CURRENT, recall=True)
    assert compare_model_performance(
        report(REFERENCE), current
    )["status"] == "unavailable"
