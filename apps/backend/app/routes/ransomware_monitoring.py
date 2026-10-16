"""Read-only access to offline synthetic ransomware monitoring evidence."""

import json
import math
from pathlib import Path

from fastapi import APIRouter


router = APIRouter()

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REPORT_PATH = (
    REPOSITORY_ROOT
    / "apps/ml-services/artifacts/ransomware/offline"
    / "rw1301_cycle2_development_drift_report.json"
)

EXPECTED_FEATURE_COUNT = 54
EXPECTED_REFERENCE_COUNT = 54
EXPECTED_CURRENT_COUNT = 54


def unavailable(reason: str) -> dict:
    return {
        "status": "unavailable",
        "analysis_type": "offline_synthetic_feature_distribution_comparison",
        "data_provenance": "synthetic_development",
        "is_live_monitoring": False,
        "reason": reason,
    }


@router.get("/api/v1/ransomware/monitoring/data-drift")
def get_data_drift() -> dict:
    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return unavailable("Offline monitoring report is missing or unreadable.")

    if not isinstance(report, dict):
        return unavailable("Offline monitoring report has an invalid structure.")

    if (
        report.get("task_id") != "RW-130-1"
        or report.get("analysis_type")
        != "offline_synthetic_feature_distribution_comparison"
        or report.get("data_provenance") != "synthetic_development"
        or report.get("is_live_monitoring") is not False
        or report.get("reference_split") != "train"
        or report.get("comparison_split") != "validation"
        or report.get("reference_count") != EXPECTED_REFERENCE_COUNT
        or report.get("current_count") != EXPECTED_CURRENT_COUNT
        or report.get("status") not in {"drift_detected", "no_drift_detected"}
    ):
        return unavailable("Offline monitoring report contract is incompatible.")

    psi = report.get("feature_psi")
    drifted = report.get("drifted_features")
    threshold = report.get("threshold")

    if (
        not isinstance(psi, dict)
        or len(psi) != EXPECTED_FEATURE_COUNT
        or not isinstance(drifted, list)
        or not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not math.isfinite(threshold)
        or threshold <= 0
    ):
        return unavailable("Offline monitoring metrics are invalid.")

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
        for value in psi.values()
    ):
        return unavailable("Offline monitoring PSI values are invalid.")

    expected_drifted = sorted(
        feature for feature, value in psi.items() if value >= threshold
    )

    if (
        drifted != expected_drifted
        or report["status"]
        != ("drift_detected" if expected_drifted else "no_drift_detected")
    ):
        return unavailable("Offline monitoring results are inconsistent.")

    return report
