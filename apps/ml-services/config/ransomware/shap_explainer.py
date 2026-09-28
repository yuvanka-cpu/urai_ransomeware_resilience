from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from catboost import CatBoostClassifier, Pool

from config.ransomware.catboost_trainer import (
    CAT_FEATURES,
    build_rows,
    load_and_verify_scenarios,
    rows_to_matrix,
)

ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "artifacts/ransomware/models/rw0704_catboost_model.cbm"
TRAINING_MANIFEST_PATH = (
    ROOT / "artifacts/ransomware/models/rw0704_catboost_training_manifest.json"
)
REPORT_PATH = (
    ROOT / "artifacts/ransomware/offline/rw0705_shap_provenance_report.json"
)
PROVENANCE_PATH = (
    ROOT / "artifacts/ransomware/offline/rw0705_feature_provenance.json"
)

TOP_FEATURES_PER_SAMPLE = 8
SAMPLE_LIMIT = 6
SHAP_TOLERANCE = 1e-10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def observable_provenance(feature_name: str) -> dict[str, object]:
    return {
        "feature_name": feature_name,
        "source_kind": "observable_event",
        "source_object": "ObservableScenarioEvent",
        "source_paths": [
            "event_family",
            "event_type",
            "attributes",
        ],
        "derivation": f"extract_window_features -> {feature_name}",
        "window_semantics": "[T-W, T] inclusive",
        "time_basis": "event_time",
        "contract": (
            "config/ransomware/shared/schemas/feature_contract.md"
        ),
        "display_allowed": True,
        "truth_or_future_field": False,
    }


def context_provenance(feature_name: str) -> dict[str, object]:
    return {
        "feature_name": feature_name,
        "source_kind": "static_scenario_metadata",
        "source_object": "FrozenScenario",
        "source_paths": [feature_name],
        "derivation": "CatBoost model-context field",
        "display_allowed": False,
        "truth_or_future_field": False,
        "reason_not_displayed": (
            "RW-070-5 displayed explanations are restricted to "
            "the frozen observable feature contract."
        ),
    }


def build_provenance(feature_names: list[str]) -> dict[str, dict[str, object]]:
    provenance = {}

    for feature in feature_names:
        provenance[feature] = observable_provenance(feature)

    for feature in CAT_FEATURES:
        provenance[feature] = context_provenance(feature)

    return provenance


def select_samples(rows):
    validation_rows = [
        row for row in rows
        if row.split == "validation"
    ]

    if len(validation_rows) < SAMPLE_LIMIT:
        raise ValueError(
            f"Expected at least {SAMPLE_LIMIT} frozen validation rows"
        )

    # Deterministic sample: first rows in generator order.
    return validation_rows[:SAMPLE_LIMIT]


def explain(model, rows, observable_features):
    matrix = rows_to_matrix(rows, observable_features)

    model_features = (
        observable_features
        + CAT_FEATURES
    )

    cat_indices = [
        len(observable_features),
        len(observable_features) + 1,
    ]

    pool = Pool(
        matrix,
        feature_names=model_features,
        cat_features=cat_indices,
    )

    shap_values = model.get_feature_importance(
        pool,
        type="ShapValues",
    )

    if shap_values.shape != (
        len(rows),
        len(model_features) + 1,
    ):
        raise ValueError(
            "Unexpected SHAP matrix shape: "
            f"{shap_values.shape}"
        )

    samples = []

    for row_index, row in enumerate(rows):
        values = shap_values[row_index]
        contributions = values[:-1]
        expected_value = float(values[-1])

        ranked = sorted(
            zip(model_features, contributions),
            key=lambda item: abs(float(item[1])),
            reverse=True,
        )

        displayed = []

        for feature_name, contribution in ranked:
            if feature_name not in observable_features:
                continue

            displayed.append(
                {
                    "feature": feature_name,
                    "shap_value": float(contribution),
                    "absolute_shap_value": abs(float(contribution)),
                }
            )

            if len(displayed) >= TOP_FEATURES_PER_SAMPLE:
                break

        probability = float(
            model.predict_proba(
                [matrix[row_index]]
            )[0][1]
        )

        samples.append(
            {
                "scenario_id": row.scenario_id,
                "split": row.split,
                "variant": row.variant,
                "window_minutes": row.window_minutes,
                "model_probability": probability,
                "expected_value": expected_value,
                "displayed_observable_features": displayed,
            }
        )

    return samples, shap_values


def validate_display_provenance(
    samples,
    provenance,
    observable_features,
):
    displayed = []

    for sample in samples:
        for item in sample["displayed_observable_features"]:
            feature = item["feature"]
            displayed.append(feature)

            if feature not in observable_features:
                raise AssertionError(
                    f"Displayed feature is not observable: {feature}"
                )

            entry = provenance.get(feature)
            if not entry:
                raise AssertionError(
                    f"Missing provenance for displayed feature: {feature}"
                )

            if entry["source_kind"] != "observable_event":
                raise AssertionError(
                    f"Displayed feature has non-observable source: {feature}"
                )

            if not entry["display_allowed"]:
                raise AssertionError(
                    f"Displayed feature is not display-allowed: {feature}"
                )

            if entry["truth_or_future_field"]:
                raise AssertionError(
                    f"Truth/future field displayed: {feature}"
                )

    if not displayed:
        raise AssertionError("No SHAP features were selected for display")

    return sorted(set(displayed))


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)

    if not TRAINING_MANIFEST_PATH.exists():
        raise FileNotFoundError(TRAINING_MANIFEST_PATH)

    _, frozen = load_and_verify_scenarios()
    rows, observable_features = build_rows(frozen)

    if len(observable_features) != 54:
        raise ValueError(
            f"Expected 54 observable features, found {len(observable_features)}"
        )

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))

    model_features = observable_features + CAT_FEATURES

    if len(model.feature_names_) != len(model_features):
        raise ValueError(
            f"Model feature count {model.get_feature_count()} "
            f"does not match expected {len(model_features)}"
        )

    provenance = build_provenance(observable_features)

    for context_feature in CAT_FEATURES:
        if context_feature not in provenance:
            raise AssertionError(
                f"Missing context provenance: {context_feature}"
            )

    samples = select_samples(rows)

    explanation_samples, shap_values = explain(
        model,
        samples,
        observable_features,
    )

    displayed_features = validate_display_provenance(
        explanation_samples,
        provenance,
        observable_features,
    )

    # Determinism check on identical model + identical samples.
    repeat_samples, repeat_shap = explain(
        model,
        samples,
        observable_features,
    )

    if not np.allclose(
        shap_values,
        repeat_shap,
        atol=SHAP_TOLERANCE,
        rtol=0.0,
    ):
        raise AssertionError(
            "Repeated SHAP generation was not deterministic"
        )

    provenance_payload = {
        "evidence_id": "RW-070-5",
        "provenance_version": "1.0",
        "observable_feature_count": len(observable_features),
        "observable_feature_names": observable_features,
        "model_context_features": CAT_FEATURES,
        "model_context_display_allowed": False,
        "features": provenance,
        "model_artifact": str(
            MODEL_PATH.relative_to(ROOT)
        ),
        "model_sha256": sha256_file(MODEL_PATH),
        "synthetic_only": True,
        "real_action_executed": False,
    }

    PROVENANCE_PATH.write_text(
        json.dumps(
            provenance_payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = {
        "evidence_id": "RW-070-5",
        "status": "pass",
        "model_artifact": str(
            MODEL_PATH.relative_to(ROOT)
        ),
        "model_sha256": sha256_file(MODEL_PATH),
        "observable_feature_count": len(observable_features),
        "model_input_feature_count": len(model_features),
        "shap_matrix_shape": list(shap_values.shape),
        "samples_generated": len(explanation_samples),
        "top_features_per_sample": TOP_FEATURES_PER_SAMPLE,
        "displayed_feature_count": len(displayed_features),
        "displayed_feature_names": displayed_features,
        "context_features_excluded_from_display": CAT_FEATURES,
        "provenance_entries": len(provenance),
        "provenance_test": True,
        "repeated_shap_deterministic": True,
        "sample_explanations": explanation_samples,
        "feature_provenance_artifact": str(
            PROVENANCE_PATH.relative_to(ROOT)
        ),
        "training_manifest": str(
            TRAINING_MANIFEST_PATH.relative_to(ROOT)
        ),
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
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

    print("RW-070-5: PASS")
    print("observable_features:", len(observable_features))
    print("model_inputs:", len(model_features))
    print("shap_matrix_shape:", tuple(shap_values.shape))
    print("samples:", len(explanation_samples))
    print("displayed_features:", len(displayed_features))
    print("context_excluded:", CAT_FEATURES)
    print("provenance_entries:", len(provenance))
    print("report:", REPORT_PATH)
    print("provenance:", PROVENANCE_PATH)
    print("model_sha256:", sha256_file(MODEL_PATH))


if __name__ == "__main__":
    main()
