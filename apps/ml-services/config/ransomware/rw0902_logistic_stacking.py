from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "artifacts" / "ransomware" / "offline" / "rw0901_oof_component_scores.json"
OUTPUT_MODEL_PATH = ROOT / "artifacts" / "ransomware" / "models" / "rw0902_logistic_stacking_model.json"
OUTPUT_REPORT_PATH = ROOT / "artifacts" / "ransomware" / "offline" / "rw0902_logistic_stacking_report.json"

SEED = 20260921

# Named evidence-layer outputs from RW-090-1.
COMPONENTS = (
    "rules",
    "anomaly",
    "catboost",
    "temporal",
    "graph",
)

FEATURE_NAMES = (
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
)


def load_oof() -> dict:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing RW-090-1 artifact: {INPUT_PATH}")

    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    if payload.get("synthetic_only") is not True:
        raise ValueError("RW-090-2 requires synthetic_only=true")

    if payload.get("development_splits") != ["train", "validation"]:
        raise ValueError("RW-090-2 must train only from train+validation OOF scores")

    rows = payload.get("rows", [])
    if len(rows) != 108:
        raise ValueError(f"Expected 108 OOF rows, found {len(rows)}")

    if any(row["split"] not in {"train", "validation"} for row in rows):
        raise ValueError("OOF rows contain a non-development split")

    if any(row["temporal_score"] is not None for row in rows):
        raise ValueError("Temporal score must remain unavailable for rejected challenger")

    return payload


def component_value(row: dict, component: str) -> tuple[float, int]:
    value = row[("rule_score" if component == "rules" else f"{component}_score")]

    if value is None:
        return 0.0, 1

    value = float(value)

    if not np.isfinite(value):
        raise ValueError(f"Non-finite {component} score in row {row['scenario_id']}")

    return value, 0


def build_matrix(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    matrix = []
    labels = []

    for row in rows:
        features = []

        for component in COMPONENTS:
            value, missing = component_value(row, component)
            features.append(value)

        for component in COMPONENTS:
            _, missing = component_value(row, component)
            features.append(missing)

        matrix.append(features)
        labels.append(int(row["label"]))

    return np.asarray(matrix, dtype=float), np.asarray(labels, dtype=int), list(FEATURE_NAMES)


def main() -> None:
    payload = load_oof()
    rows = payload["rows"]

    X, y, feature_names = build_matrix(rows)

    if X.shape != (108, 10):
        raise ValueError(f"Unexpected stacking matrix shape: {X.shape}")

    if set(np.unique(y)) != {0, 1}:
        raise ValueError(f"Expected binary labels, found {np.unique(y)}")

    # Standardize score features and leave missing indicators unscaled.
    score_columns = list(range(5))
    indicator_columns = list(range(5, 10))

    scaler = StandardScaler()
    X_scaled = X.copy()
    X_scaled[:, score_columns] = scaler.fit_transform(X[:, score_columns])

    # Regularized logistic stacking.
    model = LogisticRegression(
        C=1.0,
        solver="liblinear",
        random_state=SEED,
        max_iter=1000,
    )
    model.fit(X_scaled, y)

    probabilities = model.predict_proba(X_scaled)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    accuracy = float(np.mean(predictions == y))

    coefficients = {
        feature_names[i]: float(model.coef_[0][i])
        for i in range(len(feature_names))
    }

    scaler_mean = {
        feature_names[i]: float(scaler.mean_[i])
        for i in score_columns
    }

    scaler_scale = {
        feature_names[i]: float(scaler.scale_[i])
        for i in score_columns
    }

    model_payload = {
        "task": "RW-090-2",
        "synthetic_only": True,
        "model_type": "regularized_logistic_stacking",
        "algorithm": "sklearn.linear_model.LogisticRegression",
        "penalty": "l2",
        "C": 1.0,
        "solver": "liblinear",
        "random_seed": SEED,
        "feature_names": feature_names,
        "components": list(COMPONENTS),
        "coefficients": coefficients,
        "intercept": float(model.intercept_[0]),
        "score_standardization": {
            "columns": [feature_names[i] for i in score_columns],
            "mean": scaler_mean,
            "scale": scaler_scale,
        },
        "missing_indicator_columns": [
            feature_names[i] for i in indicator_columns
        ],
        "temporal_component_contract": {
            "status": "unavailable_rejected_challenger",
            "score_value": None,
            "missing_indicator": 1,
        },
    }

    report = {
        "task": "RW-090-2",
        "synthetic_only": True,
        "source_artifact": str(INPUT_PATH.relative_to(ROOT)),
        "training_scope": {
            "splits": ["train", "validation"],
            "oof_only": True,
            "final_holdout_used": False,
            "calibration_used": False,
        },
        "scenario_count": len({row["scenario_id"] for row in rows}),
        "row_count": len(rows),
        "matrix_shape": list(X.shape),
        "feature_count": len(feature_names),
        "components": list(COMPONENTS),
        "feature_names": feature_names,
        "missing_component_counts": {
            component: int(
                sum(component_value(row, component)[1] for row in rows)
            )
            for component in COMPONENTS
        },
        "label_counts": {
            str(label): int(np.sum(y == label))
            for label in sorted(np.unique(y))
        },
        "training_fit_accuracy": accuracy,
        "model_artifact": str(OUTPUT_MODEL_PATH.relative_to(ROOT)),
        "contract": {
            "direct_score_averaging": False,
            "regularized_logistic_stacking": True,
            "named_evidence_layers_preserved": True,
            "missing_component_indicators_preserved": True,
            "temporal_rejected_challenger_not_fabricated": True,
            "holdout_leakage": False,
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

    print(f"RW-090-2 model: {OUTPUT_MODEL_PATH}")
    print(f"RW-090-2 report: {OUTPUT_REPORT_PATH}")
    print(f"Matrix: {X.shape}")
    print(f"Scenarios: {len({row['scenario_id'] for row in rows})}")
    print(f"Temporal missing indicators: {report['missing_component_counts']['temporal']}")
    print(f"Training fit accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()
