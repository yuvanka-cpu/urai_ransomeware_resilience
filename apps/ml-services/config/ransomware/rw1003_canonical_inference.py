from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from config.ransomware.rw1001_artifact_loader import load_promoted_bundle
from config.ransomware.rw1002_feature_contract import (
    EXPECTED_FEATURES,
    validate_feature_row,
)


ROOT = Path(__file__).resolve().parents[2]

BUNDLE_DIR = ROOT / "artifacts" / "ransomware" / "promoted" / "rw0906_v1"

STACKING_MODEL_PATH = BUNDLE_DIR / "models" / "rw0902_logistic_stacking_model.json"
CALIBRATOR_PATH = BUNDLE_DIR / "models" / "rw0903_sector_calibrators.json"
THRESHOLD_PATH = BUNDLE_DIR / "offline" / "rw0904_threshold_policy_report.json"
CATBOOST_MODEL_PATH = BUNDLE_DIR / "models" / "rw0704_catboost_model.cbm"

INVESTIGATE_THRESHOLD = 0.239133
HIGH_RISK_THRESHOLD = 0.294338

COMPONENTS = (
    "rules",
    "anomaly",
    "catboost",
    "temporal",
    "graph",
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")

    return payload


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)

    z = math.exp(value)
    return z / (1.0 + z)


def _validate_sector(sector: str) -> str:
    normalized = str(sector).strip().lower()

    if normalized not in {"energy", "petrochemical"}:
        raise ValueError(
            f"Unsupported sector {sector!r}; expected energy or petrochemical"
        )

    return normalized


def _load_runtime_contracts() -> tuple[dict, dict, dict]:
    stacking = _load_json(STACKING_MODEL_PATH)
    calibrators = _load_json(CALIBRATOR_PATH)
    thresholds = _load_json(THRESHOLD_PATH)

    policy = thresholds["threshold_policy"]

    if float(policy["investigate_threshold"]) != INVESTIGATE_THRESHOLD:
        raise ValueError("RW-090-4 investigate threshold mismatch")

    if float(policy["high_risk_threshold"]) != HIGH_RISK_THRESHOLD:
        raise ValueError("RW-090-4 high-risk threshold mismatch")

    if policy["scenario_aggregation"] != "maximum_calibrated_probability":
        raise ValueError("Unsupported threshold aggregation policy")

    return stacking, calibrators, thresholds


def _build_catboost_features(
    observable_features: dict[str, Any],
    industry: str,
    site_types: str,
) -> list[Any]:
    validate_feature_row(observable_features)

    values = [observable_features[name] for name in EXPECTED_FEATURES]
    values.extend([industry, site_types])
    return values


def _catboost_probability(
    observable_features: dict[str, Any],
    industry: str,
    site_types: str,
) -> float:
    from catboost import CatBoostClassifier

    model = CatBoostClassifier()
    model.load_model(str(CATBOOST_MODEL_PATH))

    matrix = np.asarray(
        [_build_catboost_features(observable_features, industry, site_types)],
        dtype=object,
    )

    probability = float(model.predict_proba(matrix)[0, 1])

    if not math.isfinite(probability):
        raise ValueError("CatBoost produced a non-finite probability")

    return probability


def _stacking_probability(
    model_payload: dict[str, Any],
    rule_score: float,
    anomaly_score: float,
    catboost_score: float,
    graph_score: float,
) -> float:
    values = np.asarray(
        [
            rule_score,
            anomaly_score,
            catboost_score,
            0.0,
            graph_score,
        ],
        dtype=float,
    )

    missing = np.asarray(
        [0.0, 0.0, 0.0, 1.0, 0.0],
        dtype=float,
    )

    standardization = model_payload["score_standardization"]

    means = np.asarray(
        [
            standardization["mean"]["rule_score"],
            standardization["mean"]["anomaly_score"],
            standardization["mean"]["catboost_score"],
            standardization["mean"]["temporal_score"],
            standardization["mean"]["graph_score"],
        ],
        dtype=float,
    )

    scales = np.asarray(
        [
            standardization["scale"]["rule_score"],
            standardization["scale"]["anomaly_score"],
            standardization["scale"]["catboost_score"],
            standardization["scale"]["temporal_score"],
            standardization["scale"]["graph_score"],
        ],
        dtype=float,
    )

    scaled = np.zeros(5, dtype=float)

    for index in (0, 1, 2, 4):
        if scales[index] == 0:
            scaled[index] = 0.0
        else:
            scaled[index] = (values[index] - means[index]) / scales[index]

    coefficients = np.asarray(
        [
            model_payload["coefficients"]["rule_score"],
            model_payload["coefficients"]["anomaly_score"],
            model_payload["coefficients"]["catboost_score"],
            model_payload["coefficients"]["temporal_score"],
            model_payload["coefficients"]["graph_score"],
        ],
        dtype=float,
    )

    missing_coefficients = np.asarray(
        [
            model_payload["coefficients"]["rules_missing"],
            model_payload["coefficients"]["anomaly_missing"],
            model_payload["coefficients"]["catboost_missing"],
            model_payload["coefficients"]["temporal_missing"],
            model_payload["coefficients"]["graph_missing"],
        ],
        dtype=float,
    )

    logit = (
        float(model_payload["intercept"])
        + float(np.dot(coefficients, scaled))
        + float(np.dot(missing_coefficients, missing))
    )

    return _sigmoid(logit)


def _calibrate_probability(
    calibrator_payload: dict[str, Any],
    sector: str,
    probability: float,
) -> tuple[float, str]:
    sector = _validate_sector(sector)

    sector_calibrator = calibrator_payload["sector_calibrators"][sector]

    if sector_calibrator.get("status") == "sector_specific":
        calibrator = sector_calibrator
        source = "sector_specific"
    else:
        calibrator = calibrator_payload["global_calibrator"]
        source = "global_fallback"

    clipped = float(np.clip(probability, 1e-6, 1.0 - 1e-6))
    logit = math.log(clipped / (1.0 - clipped))

    calibrated = _sigmoid(
        float(calibrator["coefficient"]) * logit
        + float(calibrator["intercept"])
    )

    return float(calibrated), source


def _decision(calibrated_probability: float) -> str:
    if calibrated_probability >= HIGH_RISK_THRESHOLD:
        return "high_risk"

    if calibrated_probability >= INVESTIGATE_THRESHOLD:
        return "investigate"

    return "normal"


def canonical_inference(
    *,
    observable_features: dict[str, Any],
    industry: str,
    site_types: str,
    rule_score: float,
    anomaly_score: float,
    graph_score: float,
    sector: str,
) -> dict[str, Any]:
    validate_feature_row(observable_features)

    if not all(
        math.isfinite(float(value))
        for value in (rule_score, anomaly_score, graph_score)
    ):
        raise ValueError("Component scores must be finite")

    bundle = load_promoted_bundle()

    stacking_model, calibrators, thresholds = _load_runtime_contracts()

    catboost_score = _catboost_probability(
        observable_features,
        industry,
        site_types,
    )

    stacked_probability = _stacking_probability(
        stacking_model,
        float(rule_score),
        float(anomaly_score),
        catboost_score,
        float(graph_score),
    )

    calibrated_probability, calibration_source = _calibrate_probability(
        calibrators,
        sector,
        stacked_probability,
    )

    decision = _decision(calibrated_probability)

    return {
        "bundle_version": bundle.bundle_version,
        "task": "RW-100-3",
        "sector": _validate_sector(sector),
        "decision": decision,
        "probabilities": {
            "catboost": catboost_score,
            "stacked": stacked_probability,
            "calibrated": calibrated_probability,
        },
        "components": {
            "rule_score": float(rule_score),
            "anomaly_score": float(anomaly_score),
            "catboost_score": catboost_score,
            "temporal_score": None,
            "graph_score": float(graph_score),
            "temporal_missing": 1,
        },
        "calibration": {
            "source": calibration_source,
            "method": calibrators["method"],
        },
        "thresholds": {
            "investigate": float(
                thresholds["threshold_policy"]["investigate_threshold"]
            ),
            "high_risk": float(
                thresholds["threshold_policy"]["high_risk_threshold"]
            ),
        },
        "runtime_contract": {
            "synthetic_only": True,
            "human_approval_required": True,
            "real_action_executed": False,
            "operational_state_claimed": False,
            "physical_safety_determination": "not_determined",
        },
    }


def main() -> None:
    print("=== RW-100-3 CANONICAL INFERENCE ===")

    bundle = load_promoted_bundle()
    _load_runtime_contracts()

    print(f"Bundle: {bundle.bundle_version}")
    print(f"Validated features: {len(EXPECTED_FEATURES)}")
    print("Temporal component: unavailable")
    print(f"Investigate threshold: {INVESTIGATE_THRESHOLD}")
    print(f"High-risk threshold: {HIGH_RISK_THRESHOLD}")
    print("Status: canonical inference path ready")


if __name__ == "__main__":
    main()
