"""RW-130-2: Offline model performance drift comparison.

This module does not collect live outcomes or evaluate the frozen holdout.
"""

from math import isfinite

METRICS = ("precision", "recall", "f1", "brier")
DEFAULT_THRESHOLDS = {
    "precision": 0.10,
    "recall": 0.10,
    "f1": 0.10,
    "brier": 0.05,
}


def compare_model_performance(reference, current, thresholds=None):
    """Compare compatible, chronological, independently evaluated periods."""
    unavailable = lambda reason: {
        "status": "unavailable",
        "drift_detected": None,
        "reason": reason,
        "metric_changes": {},
    }

    if not isinstance(reference, dict) or not isinstance(current, dict):
        return unavailable("Both evaluation reports must be dictionaries.")

    required = ("model_id", "population_id", "metric_definition_id",
                "period_end", "sample_count", "metrics")

    for name, report in (("reference", reference), ("current", current)):
        if any(key not in report for key in required):
            return unavailable(f"{name} evaluation has missing required fields.")

        if any(not isinstance(report[key], str) or not report[key].strip()
               for key in required[:4]):
            return unavailable(f"{name} evaluation has invalid identifiers.")

        if type(report["sample_count"]) is not int or report["sample_count"] < 30:
            return unavailable(f"{name} evaluation has insufficient samples.")

        if not isinstance(report["metrics"], dict):
            return unavailable(f"{name} metrics must be a dictionary.")

        for metric in METRICS:
            value = report["metrics"].get(metric)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not isfinite(value) or not 0 <= value <= 1):
                return unavailable(f"{name} has invalid {metric}.")

    for field in ("model_id", "population_id", "metric_definition_id"):
        if reference[field] != current[field]:
            return unavailable(f"Incompatible {field}.")

    from datetime import datetime

    try:
        ref_end = datetime.fromisoformat(reference["period_end"])
        cur_end = datetime.fromisoformat(current["period_end"])
        if ref_end.tzinfo is None or cur_end.tzinfo is None:
            return unavailable("Period timestamps must include time zones.")
        if cur_end <= ref_end:
            return unavailable("Current evaluation must follow reference.")
    except (ValueError, TypeError):
        return unavailable("Invalid evaluation period timestamps.")

    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds is not None:
        if not isinstance(thresholds, dict) or set(thresholds) - set(METRICS):
            return unavailable("Invalid threshold configuration.")
        limits.update(thresholds)

    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not isfinite(v) or not 0 < v <= 1 for v in limits.values()):
        return unavailable("Thresholds must be finite numbers in (0, 1].")

    changes = {}
    for metric in METRICS:
        before = float(reference["metrics"][metric])
        after = float(current["metrics"][metric])
        deterioration = after - before if metric == "brier" else before - after
        changes[metric] = {
            "reference": before,
            "current": after,
            "deterioration": deterioration,
            "threshold": limits[metric],
            "degraded": deterioration > limits[metric],
        }

    detected = any(item["degraded"] for item in changes.values())
    return {
        "status": "drift_detected" if detected else "no_drift_detected",
        "drift_detected": detected,
        "reason": None,
        "metric_changes": changes,
        "scope": "offline_performance_comparison",
    }
