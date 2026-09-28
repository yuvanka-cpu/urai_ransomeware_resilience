from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from catboost import CatBoostClassifier
from sklearn.metrics import accuracy_score, log_loss, precision_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold

from config.ransomware.features.window_features import extract_window_features
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)
from config.ransomware.scenarios.scenario_registry import (
    build_frozen_scenarios,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "artifacts/ransomware/offline/split_assignment_manifest.json"
ARTIFACT_DIR = ROOT / "artifacts/ransomware/models"
REPORT_DIR = ROOT / "artifacts/ransomware/offline"

MODEL_PATH = ARTIFACT_DIR / "rw0704_catboost_model.cbm"
TRAINING_MANIFEST_PATH = ARTIFACT_DIR / "rw0704_catboost_training_manifest.json"
REPORT_PATH = REPORT_DIR / "rw0704_catboost_training_report.json"

WINDOWS = (1, 5, 15)
SEED = 20260921
CAT_FEATURES = ["industry", "site_types"]


@dataclass
class Row:
    scenario_id: str
    split: str
    variant: str
    industry: str
    site_types: str
    window_minutes: int
    label: int
    features: dict[str, float | int]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_and_verify_scenarios():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if manifest["base_seed"] != SEED:
        raise ValueError(
            f"Frozen manifest seed mismatch: {manifest['base_seed']} != {SEED}"
        )

    assignments = manifest["assignments"]
    if manifest["scenario_count"] != 80:
        raise ValueError(
            f"Expected frozen 80 scenarios, found {manifest['scenario_count']}"
        )

    asset_ids = sorted({item["asset_id"] for item in assignments})
    frozen = build_frozen_scenarios(asset_ids, base_seed=SEED)

    expected = {
        item["scenario_id"]: item
        for item in assignments
    }
    regenerated = {
        item.scenario_id: asdict(item)
        for item in frozen
    }

    if set(expected) != set(regenerated):
        raise ValueError("Regenerated scenario IDs do not match frozen manifest")

    for scenario_id, source in expected.items():
        actual = regenerated[scenario_id]
        for field in (
            "scenario_id",
            "scenario_seed",
            "use_case_id",
            "industry",
            "scenario_family",
            "variant",
            "asset_id",
            "split",
        ):
            if actual[field] != source[field]:
                raise ValueError(
                    f"Frozen scenario mismatch for {scenario_id}: "
                    f"{field}={actual[field]!r} != {source[field]!r}"
                )

    if len(regenerated) != 80:
        raise ValueError("Regenerated scenario count is not 80")

    return manifest, frozen


def build_rows(frozen):
    rows: list[Row] = []

    for scenario in frozen:
        events = assemble_scenario_events(scenario)

        if not events:
            raise ValueError(
                f"Scenario {scenario.scenario_id} generated no observable events"
            )

        end_time = datetime.fromisoformat(
            events[-1].event_time.replace("Z", "+00:00")
        )

        for window_minutes in WINDOWS:
            features = extract_window_features(
                events,
                end_time=end_time,
                duration_minutes=window_minutes,
            )

            rows.append(
                Row(
                    scenario_id=scenario.scenario_id,
                    split=scenario.split,
                    variant=scenario.variant,
                    industry=scenario.industry,
                    site_types="|".join(sorted(scenario.site_types)),
                    window_minutes=window_minutes,
                    label=1 if scenario.variant == "attack" else 0,
                    features=features,
                )
            )

    if not rows:
        raise ValueError("No training rows were generated")

    feature_names = sorted(rows[0].features)

    if len(feature_names) != 54:
        raise ValueError(
            f"Frozen feature contract expected 54 features, found {len(feature_names)}"
        )

    for row in rows:
        if sorted(row.features) != feature_names:
            raise ValueError(
                f"Feature mismatch in scenario {row.scenario_id}, "
                f"window {row.window_minutes}"
            )

    return rows, feature_names


def rows_to_matrix(rows, feature_names):
    matrix = []

    for row in rows:
        matrix.append(
            [
                row.features[name]
                for name in feature_names
            ]
            + [row.industry, row.site_types]
        )

    return matrix


def class_weights(labels: list[int]) -> list[float]:
    positives = sum(labels)
    negatives = len(labels) - positives

    if positives == 0 or negatives == 0:
        raise ValueError(
            "Training split must contain both attack and non-attack classes"
        )

    total = positives + negatives

    # Inverse-frequency weighting, normalized around 1.
    weight_negative = total / (2.0 * negatives)
    weight_positive = total / (2.0 * positives)

    return [weight_negative, weight_positive]


def grouped_cv(rows, feature_names):
    train_rows = [row for row in rows if row.split == "train"]

    groups = [row.scenario_id for row in train_rows]
    labels = [row.label for row in train_rows]

    unique_groups = sorted(set(groups))
    if len(unique_groups) < 3:
        raise ValueError("Need at least 3 training scenario groups for grouped CV")

    # Only two attack scenarios exist in the frozen train split, so
    # three grouped folds cannot all contain both classes.
    splitter = StratifiedGroupKFold(
        n_splits=2,
        shuffle=True,
        random_state=SEED,
    )

    X = rows_to_matrix(train_rows, feature_names)
    y = labels

    cat_indices = [
        len(feature_names),
        len(feature_names) + 1,
    ]

    fold_results = []

    for fold, (fit_idx, val_idx) in enumerate(
        splitter.split(X, y, groups=groups),
        start=1,
    ):
        y_fit = [y[i] for i in fit_idx]
        y_val = [y[i] for i in val_idx]

        if len(set(y_fit)) < 2 or len(set(y_val)) < 2:
            raise ValueError(
                f"Grouped fold {fold} lacks both classes"
            )

        weights = class_weights(y_fit)

        model = CatBoostClassifier(
            loss_function="Logloss",
            eval_metric="Logloss",
            iterations=200,
            depth=5,
            learning_rate=0.05,
            l2_leaf_reg=3.0,
            random_seed=SEED,
            class_weights=weights,
            cat_features=cat_indices,
            thread_count=1,
            verbose=False,
            allow_writing_files=False,
        )

        model.fit(
            [X[i] for i in fit_idx],
            y_fit,
            eval_set=([X[i] for i in val_idx], y_val),
            use_best_model=True,
            verbose=False,
        )

        probability = model.predict_proba(
            [X[i] for i in val_idx]
        )[:, 1]

        predicted = (probability >= 0.5).astype(int)

        fold_results.append(
            {
                "fold": fold,
                "fit_scenarios": len(
                    {groups[i] for i in fit_idx}
                ),
                "validation_scenarios": len(
                    {groups[i] for i in val_idx}
                ),
                "validation_rows": len(val_idx),
                "accuracy": accuracy_score(y_val, predicted),
                "precision": precision_score(
                    y_val, predicted, zero_division=0
                ),
                "recall": recall_score(
                    y_val, predicted, zero_division=0
                ),
                "log_loss": log_loss(y_val, probability),
            }
        )

    return fold_results


def train_final(rows, feature_names):
    train_rows = [row for row in rows if row.split == "train"]
    validation_rows = [
        row for row in rows if row.split == "validation"
    ]

    train_scenarios = {row.scenario_id for row in train_rows}
    validation_scenarios = {
        row.scenario_id for row in validation_rows
    }

    overlap = train_scenarios & validation_scenarios
    if overlap:
        raise ValueError(
            f"Scenario leakage between train and validation: {sorted(overlap)}"
        )

    X_train = rows_to_matrix(train_rows, feature_names)
    y_train = [row.label for row in train_rows]

    X_validation = rows_to_matrix(
        validation_rows,
        feature_names,
    )
    y_validation = [row.label for row in validation_rows]

    if len(set(y_train)) < 2:
        raise ValueError("Training split contains only one class")

    weights = class_weights(y_train)

    cat_indices = [
        len(feature_names),
        len(feature_names) + 1,
    ]

    model = CatBoostClassifier(
        loss_function="Logloss",
        eval_metric="Logloss",
        iterations=200,
        depth=5,
        learning_rate=0.05,
        l2_leaf_reg=3.0,
        random_seed=SEED,
        class_weights=weights,
        cat_features=cat_indices,
        thread_count=1,
        verbose=False,
        allow_writing_files=False,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=(X_validation, y_validation),
        use_best_model=True,
        verbose=False,
    )

    model.save_model(MODEL_PATH)

    probability = model.predict_proba(X_validation)[:, 1]
    predicted = (probability >= 0.5).astype(int)

    validation_report = {
        "validation_rows": len(validation_rows),
        "validation_scenarios": len(validation_scenarios),
        "accuracy": accuracy_score(y_validation, predicted),
        "precision": precision_score(
            y_validation,
            predicted,
            zero_division=0,
        ),
        "recall": recall_score(
            y_validation,
            predicted,
            zero_division=0,
        ),
        "log_loss": log_loss(
            y_validation,
            probability,
        ),
    }

    return model, weights, validation_report


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    manifest, frozen = load_and_verify_scenarios()
    rows, feature_names = build_rows(frozen)

    split_counts = {}
    variant_counts = {}

    for row in rows:
        split_counts[row.split] = split_counts.get(row.split, 0) + 1
        key = f"{row.split}:{row.variant}"
        variant_counts[key] = variant_counts.get(key, 0) + 1

    cv_results = grouped_cv(rows, feature_names)
    model, weights, validation_report = train_final(
        rows,
        feature_names,
    )

    training_manifest = {
        "evidence_id": "RW-070-4",
        "artifact_type": "catboost_training_manifest",
        "manifest_version": "1.0",
        "base_seed": SEED,
        "source_split_manifest": str(
            MANIFEST_PATH.relative_to(ROOT)
        ),
        "source_split_manifest_sha256": sha256_file(MANIFEST_PATH),
        "scenario_count": len(frozen),
        "generated_row_count": len(rows),
        "windows_minutes": list(WINDOWS),
        "observable_feature_count": len(feature_names),
        "observable_feature_names": feature_names,
        "categorical_context_features": CAT_FEATURES,
        "model_input_feature_count": len(feature_names) + len(CAT_FEATURES),
        "target_field": "variant == attack",
        "group_field": "scenario_id",
        "label_leakage_excluded": True,
        "scenario_group_leakage_excluded": True,
        "splits_used_for_training": ["train"],
        "split_used_for_frozen_validation": "validation",
        "class_weights": weights,
        "catboost_version": model.get_metadata().get(
            "train_params",
            {},
        ).get("catboost_version", "1.2.10"),
        "parameters": {
            "loss_function": "Logloss",
            "eval_metric": "Logloss",
            "iterations": 200,
            "depth": 5,
            "learning_rate": 0.05,
            "l2_leaf_reg": 3.0,
            "random_seed": SEED,
            "thread_count": 1,
        },
        "split_row_counts": split_counts,
        "variant_row_counts": variant_counts,
        "grouped_cv": cv_results,
        "frozen_validation": validation_report,
        "synthetic_only": True,
        "real_action_executed": False,
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    model_hash = sha256_file(MODEL_PATH)
    training_manifest["model_sha256"] = model_hash

    TRAINING_MANIFEST_PATH.write_text(
        json.dumps(
            training_manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = {
        "evidence_id": "RW-070-4",
        "status": "pass",
        "scenario_count": len(frozen),
        "row_count": len(rows),
        "observable_feature_count": len(feature_names),
        "categorical_context_features": CAT_FEATURES,
        "group_field": "scenario_id",
        "class_weighting": True,
        "scenario_grouped_validation": True,
        "cv_folds": cv_results,
        "frozen_validation": validation_report,
        "model_artifact": str(
            MODEL_PATH.relative_to(ROOT)
        ),
        "training_manifest": str(
            TRAINING_MANIFEST_PATH.relative_to(ROOT)
        ),
        "model_sha256": model_hash,
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

    print("RW-070-4: PASS")
    print("scenarios:", len(frozen))
    print("rows:", len(rows))
    print("observable_features:", len(feature_names))
    print("categorical_context:", CAT_FEATURES)
    print("grouped_cv_folds:", len(cv_results))
    print("model:", MODEL_PATH)
    print("manifest:", TRAINING_MANIFEST_PATH)
    print("report:", REPORT_PATH)
    print("model_sha256:", model_hash)


if __name__ == "__main__":
    main()
