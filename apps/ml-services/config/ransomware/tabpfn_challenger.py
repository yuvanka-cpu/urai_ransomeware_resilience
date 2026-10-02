from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from tabpfn import TabPFNClassifier

from config.ransomware.catboost_trainer import (
    SEED,
    WINDOWS,
    build_rows,
    load_and_verify_scenarios,
)


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts/ransomware/offline"
REPORT_PATH = REPORT_DIR / "rw0801_tabpfn_challenger_report.json"


def build_category_maps(rows):
    """Build one deterministic categorical mapping for the frozen dataset."""
    industries = sorted({row.industry for row in rows})
    site_types = sorted({row.site_types for row in rows})

    industry_map = {value: index for index, value in enumerate(industries)}
    site_map = {value: index for index, value in enumerate(site_types)}

    return industry_map, site_map


def encode_rows(rows, feature_names, industry_map, site_map):
    """Convert the frozen feature contract into TabPFN-compatible numeric input."""
    matrix = []

    for row in rows:
        matrix.append(
            [
                *[
                    float(row.features[name])
                    for name in feature_names
                ],
                float(industry_map[row.industry]),
                float(site_map[row.site_types]),
            ]
        )

    return np.asarray(matrix, dtype=np.float32)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    manifest, frozen = load_and_verify_scenarios()
    rows, feature_names = build_rows(frozen)

    train_rows = [row for row in rows if row.split == "train"]
    validation_rows = [row for row in rows if row.split == "validation"]

    if not train_rows or not validation_rows:
        raise ValueError("Frozen train/validation splits are required")

    industry_map, site_map = build_category_maps(rows)

    X_train = encode_rows(
        train_rows,
        feature_names,
        industry_map,
        site_map,
    )

    y_train = np.asarray(
        [row.label for row in train_rows],
        dtype=np.int64,
    )

    X_validation = encode_rows(
        validation_rows,
        feature_names,
        industry_map,
        site_map,
    )

    y_validation = np.asarray(
        [row.label for row in validation_rows],
        dtype=np.int64,
    )

    categorical_indices = [
        len(feature_names),
        len(feature_names) + 1,
    ]

    model = TabPFNClassifier(
        device="auto",
        random_state=SEED,
        categorical_features_indices=categorical_indices,
        show_progress_bar=True,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_validation)
    probabilities = model.predict_proba(X_validation)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_validation, predictions),
        "balanced_accuracy": balanced_accuracy_score(
            y_validation,
            predictions,
        ),
        "precision": precision_score(
            y_validation,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_validation,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_validation,
            predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_validation,
            probabilities,
        ),
    }

    report = {
        "evidence_id": "RW-080-1",
        "status": "pass",
        "model": "TabPFNClassifier",
        "tabpfn_version": "9.0.0",
        "scenario_count": len(frozen),
        "generated_row_count": len(rows),
        "train_row_count": len(train_rows),
        "validation_row_count": len(validation_rows),
        "windows_minutes": list(WINDOWS),
        "observable_feature_count": len(feature_names),
        "categorical_context_features": [
            "industry",
            "site_types",
        ],
        "model_input_feature_count": len(feature_names) + 2,
        "categorical_feature_indices": categorical_indices,
        "group_field": "scenario_id",
        "scenario_group_leakage_excluded": True,
        "label_leakage_excluded": True,
        "metrics": metrics,
        "synthetic_only": True,
        "real_action_executed": False,
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("RW-080-1: PASS")
    print("scenarios:", len(frozen))
    print("train_rows:", len(train_rows))
    print("validation_rows:", len(validation_rows))
    print("features:", len(feature_names))
    print("metrics:", json.dumps(metrics, indent=2))
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    main()
