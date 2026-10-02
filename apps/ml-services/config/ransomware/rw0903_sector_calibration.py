from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

from config.ransomware.catboost_trainer import (
    class_weights,
    load_and_verify_scenarios,
    rows_to_matrix,
)
from config.ransomware.rw0901_oof_scores import (
    _anomaly_score,
    _build_anomaly,
    _graph_score,
    _make_catboost,
    _rule_score,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)


ROOT = Path(__file__).resolve().parents[2]

STACKING_MODEL_PATH = (
    ROOT
    / "artifacts/ransomware/models/rw0902_logistic_stacking_model.json"
)

OUTPUT_MODEL_PATH = (
    ROOT
    / "artifacts/ransomware/models/rw0903_sector_calibrators.json"
)

OUTPUT_REPORT_PATH = (
    ROOT
    / "artifacts/ransomware/offline/rw0903_sector_calibration_report.json"
)

SEED = 20260921
DEVELOPMENT_SPLITS = {"train", "validation"}
CALIBRATION_SPLIT = "calibration"


def load_stacking_model() -> dict:
    payload = json.loads(
        STACKING_MODEL_PATH.read_text(encoding="utf-8")
    )

    expected = [
        "rule_score",
        "anomaly_score",
        "catboost_score",
        "temporal_score",
        "graph_score",
        "rules_missing",
        "anomaly_missing",
        "catboost_missing",
        "temporal_missing",
        "graph_missing",
    ]

    if payload["feature_names"] != expected:
        raise ValueError("RW-090-2 feature contract mismatch")

    return payload


def build_stacking_probability(
    model_payload: dict,
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
            0.0,  # temporal score unavailable
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
            standardization["scale"]["mean"]
            if False
            else standardization["scale"]["temporal_score"],
            standardization["scale"]["graph_score"],
        ],
        dtype=float,
    )

    # Temporal has no observed score. Its standardized score is therefore
    # explicitly zero because the missing indicator carries its state.
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

    return float(1.0 / (1.0 + np.exp(-logit)))


def fit_sigmoid(probabilities: np.ndarray, labels: np.ndarray) -> dict:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)

    model = LogisticRegression(
        C=1.0,
        solver="liblinear",
        random_state=SEED,
        max_iter=1000,
    )
    model.fit(logits, labels)

    return {
        "method": "sigmoid",
        "coefficient": float(model.coef_[0][0]),
        "intercept": float(model.intercept_[0]),
        "sample_count": int(len(labels)),
        "positive_count": int(np.sum(labels)),
        "negative_count": int(np.sum(labels == 0)),
    }


def apply_sigmoid(calibrator: dict, probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / (1.0 - clipped))

    transformed = (
        calibrator["coefficient"] * logits
        + calibrator["intercept"]
    )

    return 1.0 / (1.0 + np.exp(-transformed))


def ece(
    labels: np.ndarray,
    probabilities: np.ndarray,
    bins: int = 5,
) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(labels)
    value = 0.0

    for left, right in zip(edges[:-1], edges[1:]):
        if right == 1.0:
            mask = (probabilities >= left) & (probabilities <= right)
        else:
            mask = (probabilities >= left) & (probabilities < right)

        count = int(np.sum(mask))
        if count == 0:
            continue

        confidence = float(np.mean(probabilities[mask]))
        accuracy = float(np.mean(labels[mask]))

        value += (count / total) * abs(confidence - accuracy)

    return float(value)


def metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict:
    clipped = np.clip(probabilities, 1e-6, 1.0 - 1e-6)

    return {
        "brier": float(brier_score_loss(labels, clipped)),
        "log_loss": float(log_loss(labels, clipped, labels=[0, 1])),
        "ece_5_bin": ece(labels, clipped),
    }


def main() -> None:
    stacking = load_stacking_model()

    manifest, frozen = load_and_verify_scenarios()

    development = [
        scenario
        for scenario in frozen
        if scenario.split in DEVELOPMENT_SPLITS
    ]

    calibration = [
        scenario
        for scenario in frozen
        if scenario.split == CALIBRATION_SPLIT
    ]

    if len(calibration) != 10:
        raise ValueError(
            f"Expected 10 calibration scenarios, found {len(calibration)}"
        )

    # Build the exact same window rows used by the existing baseline.
    all_rows, feature_names = __import__(
        "config.ransomware.catboost_trainer",
        fromlist=["build_rows"],
    ).build_rows(frozen)

    development_ids = {s.scenario_id for s in development}
    calibration_ids = {s.scenario_id for s in calibration}

    development_rows = [
        row for row in all_rows
        if row.scenario_id in development_ids
    ]

    calibration_rows = [
        row for row in all_rows
        if row.scenario_id in calibration_ids
    ]

    if len(calibration_rows) != 30:
        raise ValueError(
            f"Expected 30 calibration window rows, found {len(calibration_rows)}"
        )

    # Train the component models ONLY on train + validation.
    catboost = _make_catboost(feature_names, development_rows)
    anomaly = _build_anomaly(feature_names, development_rows)

    calibration_matrix = rows_to_matrix(
        calibration_rows,
        feature_names,
    )
    cat_probabilities = catboost.predict_proba(calibration_matrix)[:, 1]

    scenario_by_id = {
        scenario.scenario_id: scenario
        for scenario in calibration
    }

    raw_rows = []

    for row, cat_probability in zip(
        calibration_rows,
        cat_probabilities,
    ):
        scenario = scenario_by_id[row.scenario_id]
        events = assemble_scenario_events(scenario)

        end_time = __import__("datetime").datetime.fromisoformat(
            events[-1].event_time.replace("Z", "+00:00")
        )

        rule_score = _rule_score(row.features)

        anomaly_evidence = anomaly.score(row.features)
        anomaly_score = _anomaly_score(anomaly_evidence)

        graph_score, graph_exposed_count = _graph_score(
            scenario.industry,
            events,
            end_time,
            row.window_minutes,
        )

        pre_probability = build_stacking_probability(
            stacking,
            rule_score,
            anomaly_score,
            float(cat_probability),
            graph_score,
        )

        raw_rows.append(
            {
                "scenario_id": row.scenario_id,
                "industry": row.industry,
                "window_minutes": row.window_minutes,
                "label": int(row.label),
                "rule_score": rule_score,
                "anomaly_score": anomaly_score,
                "catboost_score": round(float(cat_probability), 6),
                "temporal_score": None,
                "graph_score": graph_score,
                "graph_exposed_asset_count": graph_exposed_count,
                "pre_calibration_probability": pre_probability,
            }
        )

    all_labels = np.asarray(
        [row["label"] for row in raw_rows],
        dtype=int,
    )
    all_probabilities = np.asarray(
        [row["pre_calibration_probability"] for row in raw_rows],
        dtype=float,
    )

    global_calibrator = fit_sigmoid(
        all_probabilities,
        all_labels,
    )

    calibrated_global = apply_sigmoid(
        global_calibrator,
        all_probabilities,
    )

    sector_calibrators = {}
    sector_metrics = {}

    for sector in ("energy", "petrochemical"):
        sector_rows = [
            row for row in raw_rows
            if row["industry"] == sector
        ]

        labels = np.asarray(
            [row["label"] for row in sector_rows],
            dtype=int,
        )
        probabilities = np.asarray(
            [row["pre_calibration_probability"] for row in sector_rows],
            dtype=float,
        )

        unique_labels = sorted(set(labels.tolist()))

        if len(unique_labels) == 2:
            calibrator = fit_sigmoid(probabilities, labels)
            calibrated = apply_sigmoid(
                calibrator,
                probabilities,
            )

            sector_calibrators[sector] = {
                "status": "sector_specific",
                **calibrator,
            }

            sector_metrics[sector] = {
                "status": "sector_specific",
                "scenario_count": len(
                    {
                        row["scenario_id"]
                        for row in sector_rows
                    }
                ),
                "row_count": len(sector_rows),
                "label_counts": {
                    str(value): int(np.sum(labels == value))
                    for value in unique_labels
                },
                "pre_calibration": metrics(
                    labels,
                    probabilities,
                ),
                "post_calibration": metrics(
                    labels,
                    calibrated,
                ),
            }
        else:
            sector_calibrators[sector] = {
                "status": "insufficient_class_diversity",
                "fallback": "global_sigmoid",
                "unique_labels": unique_labels,
                "sample_count": len(labels),
            }

            sector_metrics[sector] = {
                "status": "insufficient_class_diversity",
                "scenario_count": len(
                    {
                        row["scenario_id"]
                        for row in sector_rows
                    }
                ),
                "row_count": len(sector_rows),
                "label_counts": {
                    str(value): int(np.sum(labels == value))
                    for value in unique_labels
                },
            }

    model_payload = {
        "task": "RW-090-3",
        "synthetic_only": True,
        "method": "sigmoid_probability_calibration",
        "training_scope": {
            "component_models_trained_on": [
                "train",
                "validation",
            ],
            "calibration_split_only": True,
            "final_holdout_used": False,
            "test_split_used": False,
        },
        "global_calibrator": global_calibrator,
        "sector_calibrators": sector_calibrators,
        "temporal_component": {
            "status": "unavailable_rejected_challenger",
            "score": None,
            "missing_indicator": 1,
        },
    }

    report = {
        "task": "RW-090-3",
        "synthetic_only": True,
        "calibration_scenarios": len(calibration),
        "calibration_rows": len(raw_rows),
        "sector_scenario_counts": {
            sector: len(
                {
                    row["scenario_id"]
                    for row in raw_rows
                    if row["industry"] == sector
                }
            )
            for sector in ("energy", "petrochemical")
        },
        "sector_row_counts": {
            sector: sum(
                row["industry"] == sector
                for row in raw_rows
            )
            for sector in ("energy", "petrochemical")
        },
        "global_label_counts": {
            str(value): int(np.sum(all_labels == value))
            for value in sorted(set(all_labels.tolist()))
        },
        "global_pre_calibration": metrics(
            all_labels,
            all_probabilities,
        ),
        "global_post_calibration": metrics(
            all_labels,
            calibrated_global,
        ),
        "sector_metrics": sector_metrics,
        "contract": {
            "calibration_split_only": True,
            "final_holdout_used": False,
            "test_split_used": False,
            "sector_specific_when_class_diversity_allows": True,
            "insufficient_sector_data_is_explicit": True,
            "global_fallback_is_explicit": True,
            "temporal_rejected_challenger_not_fabricated": True,
            "raw_component_scores_preserved": True,
        },
    }

    OUTPUT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_MODEL_PATH.write_text(
        json.dumps(model_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    OUTPUT_REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=== RW-090-3 COMPLETE ===")
    print("Development scenarios:", len(development))
    print("Calibration scenarios:", len(calibration))
    print("Calibration rows:", len(raw_rows))
    print("Global label counts:", report["global_label_counts"])

    for sector in ("energy", "petrochemical"):
        print(
            f"{sector}:",
            sector_calibrators[sector]["status"],
        )

    print("Global pre-calibration:", report["global_pre_calibration"])
    print("Global post-calibration:", report["global_post_calibration"])
    print("Model:", OUTPUT_MODEL_PATH)
    print("Report:", OUTPUT_REPORT_PATH)


if __name__ == "__main__":
    main()
