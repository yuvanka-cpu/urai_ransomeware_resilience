from __future__ import annotations

import hashlib
import json
from datetime import datetime
from datetime import datetime
from pathlib import Path
from typing import Any

from catboost import CatBoostClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from config.ransomware.catboost_trainer import (
    build_rows,
    load_and_verify_scenarios,
)
from config.ransomware.features.window_features import extract_window_features
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)
from config.ransomware.scenarios.scenario_registry import (
    asdict,
)

try:
    from config.ransomware.scenarios.lifecycle_generator import LIFECYCLE_STAGES
except ImportError:
    LIFECYCLE_STAGES = (
        "initial_access",
        "execution_persistence",
        "privilege_escalation",
        "discovery",
        "lateral_movement",
        "staging",
        "recovery_impairment",
        "encryption_impact",
        "extortion_marker",
        "recovery",
    )

try:
    from config.ransomware.scenarios.benign_generator import BENIGN_SCENARIO_FAMILIES
except ImportError:
    BENIGN_SCENARIO_FAMILIES = (
        "patching",
        "deployment",
        "bulk_copy",
        "compression",
        "backup",
        "restore_test",
        "approved_administration",
        "vendor_support",
        "relay_configuration_work",
        "turnaround_work",
        "failover",
        "historian_replay",
        "campaign_changes",
    )


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT / "artifacts/ransomware/models/rw0704_catboost_model.cbm"
)
TRAINING_MANIFEST_PATH = (
    ROOT
    / "artifacts/ransomware/models/rw0704_catboost_training_manifest.json"
)
SOURCE_SPLIT_MANIFEST_PATH = (
    ROOT
    / "artifacts/ransomware/offline/split_assignment_manifest.json"
)
REPORT_PATH = (
    ROOT
    / "artifacts/ransomware/offline/rw0706_evaluation_scorecard.json"
)

ENERGY_ASSETS_PATH = ROOT / "config/ransomware/energy/assets.json"
PETROCHEMICAL_ASSETS_PATH = (
    ROOT / "config/ransomware/petrochemical/assets.json"
)

WINDOWS = (1, 5, 15)
THRESHOLD = 0.5
SEED = 20260921
EXPECTED_OBSERVABLE_FEATURE_COUNT = 54
SEALED_SPLIT = "untouched_holdout"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inventory() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for path in (ENERGY_ASSETS_PATH, PETROCHEMICAL_ASSETS_PATH):
        payload = load_json(path)
        for asset in payload["assets"]:
            result[asset["asset_id"]] = {
                **asset,
                "sector": payload["sector"],
            }

    return result


def model_matrix(
    rows: list[Any],
    feature_names: list[str],
) -> list[list[Any]]:
    matrix: list[list[Any]] = []

    for row in rows:
        matrix.append(
            [
                row.features[name]
                for name in feature_names
            ]
            + [row.industry, row.site_types]
        )

    return matrix


def metric_bundle(
    labels: list[int],
    probabilities: list[float],
    threshold: float = THRESHOLD,
) -> dict[str, Any]:
    predicted = [1 if value >= threshold else 0 for value in probabilities]

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predicted,
        labels=[0, 1],
    ).ravel()

    has_both_classes = len(set(labels)) == 2

    result: dict[str, Any] = {
        "rows": len(labels),
        "positive_rows": sum(labels),
        "negative_rows": len(labels) - sum(labels),
        "threshold": threshold,
        "accuracy": accuracy_score(labels, predicted),
        "precision": precision_score(
            labels,
            predicted,
            zero_division=0,
        ),
        "recall": recall_score(
            labels,
            predicted,
            zero_division=0,
        ),
        "f1": f1_score(
            labels,
            predicted,
            zero_division=0,
        ),
        "balanced_accuracy": (
            balanced_accuracy_score(labels, predicted)
            if has_both_classes
            else None
        ),
        "fpr": (
            fp / (fp + tn)
            if (fp + tn)
            else None
        ),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "roc_auc": (
            roc_auc_score(labels, probabilities)
            if has_both_classes
            else None
        ),
        "pr_auc": (
            average_precision_score(labels, probabilities)
            if has_both_classes
            else None
        ),
    }

    return result


def score_matrix(
    model: CatBoostClassifier,
    matrix: list[list[Any]],
) -> list[float]:
    if not matrix:
        return []

    probabilities = model.predict_proba(matrix)[:, 1]
    return [float(value) for value in probabilities]


def resolve_asset(
    asset_id: str,
    inventory: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return inventory.get(asset_id)


def slice_scorecard(
    scored_rows: list[dict[str, Any]],
    key: str,
) -> dict[str, Any]:
    values = sorted(
        {
            row[key]
            for row in scored_rows
            if row.get(key) is not None
        }
    )

    scorecards: dict[str, Any] = {}

    for value in values:
        subset = [
            row
            for row in scored_rows
            if row.get(key) == value
        ]

        labels = [int(row["label"]) for row in subset]
        probabilities = [
            float(row["probability"])
            for row in subset
        ]

        scorecards[str(value)] = metric_bundle(
            labels,
            probabilities,
        )

    return scorecards


def build_anchor_matrix(
    scenario: Any,
    anchor_time: Any,
    feature_names: list[str],
) -> list[list[Any]]:
    events = assemble_scenario_events(scenario)

    rows: list[list[Any]] = []

    for window_minutes in WINDOWS:
        parsed_anchor_time = anchor_time if isinstance(anchor_time, datetime) else datetime.fromisoformat(str(anchor_time).replace("Z", "+00:00"))

        features = extract_window_features(
            events,
            end_time=parsed_anchor_time,
            duration_minutes=window_minutes,
        )

        if sorted(features) != feature_names:
            raise ValueError(
                "Feature contract mismatch during anchored evaluation"
            )

        rows.append(
            [
                features[name]
                for name in feature_names
            ]
            + [
                scenario.industry,
                "|".join(sorted(scenario.site_types)),
            ]
        )

    return rows


def build_stage_scorecards(
    model: CatBoostClassifier,
    attack_scenarios: list[Any],
    feature_names: list[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for stage_index, stage_name in enumerate(LIFECYCLE_STAGES):
        labels: list[int] = []
        probabilities: list[float] = []
        anchor_event_types: set[str] = set()

        for scenario in attack_scenarios:
            events = assemble_scenario_events(scenario)

            if stage_index >= len(events):
                raise ValueError(
                    f"Missing lifecycle event index {stage_index} "
                    f"for scenario {scenario.scenario_id}"
                )

            anchor = events[stage_index]
            anchor_event_types.add(anchor.event_type)

            matrix = build_anchor_matrix(
                scenario,
                anchor.event_time,
                feature_names,
            )

            probabilities.extend(score_matrix(model, matrix))
            labels.extend([1] * len(WINDOWS))

        bundle = metric_bundle(
            labels,
            probabilities,
        )

        bundle["attack_scenarios"] = len(attack_scenarios)
        bundle["windows_per_scenario"] = len(WINDOWS)
        bundle["anchor_event_types"] = sorted(anchor_event_types)
        bundle["stage_index"] = stage_index
        bundle["stage_name"] = stage_name

        result[stage_name] = bundle

    return result


def build_benign_family_fpr(
    model: CatBoostClassifier,
    benign_scenarios: list[Any],
    feature_names: list[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for family_index, family_name in enumerate(
        BENIGN_SCENARIO_FAMILIES
    ):
        labels: list[int] = []
        probabilities: list[float] = []
        anchor_event_types: set[str] = set()

        for scenario in benign_scenarios:
            events = assemble_scenario_events(scenario)

            if family_index >= len(events):
                raise ValueError(
                    f"Missing benign-family event index {family_index} "
                    f"for scenario {scenario.scenario_id}"
                )

            anchor = events[family_index]
            anchor_event_types.add(anchor.event_type)

            matrix = build_anchor_matrix(
                scenario,
                anchor.event_time,
                feature_names,
            )

            probabilities.extend(score_matrix(model, matrix))
            labels.extend([0] * len(WINDOWS))

        bundle = metric_bundle(
            labels,
            probabilities,
        )

        result[family_name] = {
            "rows": bundle["rows"],
            "benign_scenarios": len(benign_scenarios),
            "windows_per_family_event": len(WINDOWS),
            "false_positive_count": (
                bundle["confusion_matrix"]["fp"]
            ),
            "false_positive_rate": bundle["fpr"],
            "threshold": THRESHOLD,
            "anchor_event_types": sorted(anchor_event_types),
            "interpretation": (
                "FPR for windows ending on/containing the named "
                "benign-family event; these are not isolated-operation "
                "windows because the feature window may include nearby "
                "observable events."
            ),
        }

    return result


def build_standard_test_rows(
    model: CatBoostClassifier,
    rows: list[Any],
    feature_names: list[str],
) -> list[dict[str, Any]]:
    test_rows = [
        row
        for row in rows
        if row.split == "test"
    ]

    if any(row.split == SEALED_SPLIT for row in test_rows):
        raise ValueError(
            "Untouched holdout contaminated standard test evaluation"
        )

    matrix = model_matrix(
        test_rows,
        feature_names,
    )
    probabilities = score_matrix(
        model,
        matrix,
    )

    inventory = load_inventory()
    scored: list[dict[str, Any]] = []

    for row, probability in zip(
        test_rows,
        probabilities,
        strict=True,
    ):
        predicted = int(probability >= THRESHOLD)

        scored.append(
            {
                "scenario_id": row.scenario_id,
                "industry": row.industry,
                "site_type": row.site_types,
                "label": int(row.label),
                "probability": probability,
                "predicted": predicted,
                "asset_id": None,
                "site_id": None,
                "zone": None,
                "asset_type": None,
            }
        )

    return scored


def attach_asset_context(
    scored_rows: list[dict[str, Any]],
    frozen: list[Any],
) -> None:
    inventory = load_inventory()
    scenario_map = {
        scenario.scenario_id: scenario
        for scenario in frozen
        if scenario.split == "test"
    }

    for row in scored_rows:
        scenario = scenario_map[row["scenario_id"]]
        asset = resolve_asset(
            scenario.asset_id,
            inventory,
        )

        row["asset_id"] = scenario.asset_id

        if asset is None:
            continue

        row["site_id"] = asset["site_id"]
        row["zone"] = asset["zone"]
        row["asset_type"] = asset["asset_type"]


def main() -> None:
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_manifest = load_json(
        SOURCE_SPLIT_MANIFEST_PATH
    )
    training_manifest = load_json(
        TRAINING_MANIFEST_PATH
    )

    if source_manifest["base_seed"] != SEED:
        raise ValueError(
            "Frozen split manifest seed mismatch"
        )

    if source_manifest["scenario_count"] != 80:
        raise ValueError(
            "Expected frozen 80-scenario manifest"
        )

    if training_manifest["base_seed"] != SEED:
        raise ValueError(
            "Training manifest seed mismatch"
        )

    feature_names = list(
        training_manifest["observable_feature_names"]
    )

    if len(feature_names) != EXPECTED_OBSERVABLE_FEATURE_COUNT:
        raise ValueError(
            "Training manifest does not contain the "
            "expected 54 observable features"
        )

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))

    if len(model.feature_names_) != (
        len(feature_names) + 2
    ):
        raise ValueError(
            "Saved CatBoost model input width does not match "
            "54 observable + 2 categorical context fields"
        )

    model_sha256 = sha256_file(MODEL_PATH)

    manifest_model_sha = training_manifest.get(
        "model_sha256",
        model_sha256,
    )

    if (
        manifest_model_sha != model_sha256
        and "model_sha256" in training_manifest
    ):
        raise ValueError(
            "Saved CatBoost model SHA-256 does not match "
            "training manifest"
        )

    _, frozen = load_and_verify_scenarios()
    rows, regenerated_feature_names = build_rows(
        frozen
    )

    if regenerated_feature_names != feature_names:
        raise ValueError(
            "Regenerated feature names differ from "
            "the RW-070-4 training manifest"
        )

    test_scenarios = [
        scenario
        for scenario in frozen
        if scenario.split == "test"
    ]
    attack_scenarios = [
        scenario
        for scenario in test_scenarios
        if scenario.variant == "attack"
    ]
    benign_scenarios = [
        scenario
        for scenario in test_scenarios
        if scenario.variant == "benign"
    ]

    if len(test_scenarios) != 14:
        raise ValueError(
            f"Expected 14 frozen test scenarios, found "
            f"{len(test_scenarios)}"
        )

    scored_rows = build_standard_test_rows(
        model,
        rows,
        feature_names,
    )

    attach_asset_context(
        scored_rows,
        frozen,
    )

    labels = [
        int(row["label"])
        for row in scored_rows
    ]
    probabilities = [
        float(row["probability"])
        for row in scored_rows
    ]

    unresolved_asset_ids = sorted(
        {
            scenario.asset_id
            for scenario in test_scenarios
            if scenario.asset_id
            not in load_inventory()
        }
    )

    report = {
        "evidence_id": "RW-070-6",
        "artifact_type": "evaluation_scorecard",
        "report_version": "1.0",
        "base_seed": SEED,
        "threshold": THRESHOLD,
        "windows_minutes": list(WINDOWS),
        "evaluated_split": "test",
        "sealed_split": {
            "name": SEALED_SPLIT,
            "status": "sealed_not_evaluated",
        },
        "source_split_manifest": str(
            SOURCE_SPLIT_MANIFEST_PATH.relative_to(ROOT)
        ),
        "source_split_manifest_sha256": sha256_file(
            SOURCE_SPLIT_MANIFEST_PATH
        ),
        "training_manifest": str(
            TRAINING_MANIFEST_PATH.relative_to(ROOT)
        ),
        "training_manifest_sha256": sha256_file(
            TRAINING_MANIFEST_PATH
        ),
        "model_path": str(
            MODEL_PATH.relative_to(ROOT)
        ),
        "model_sha256": model_sha256,
        "observable_feature_count": len(feature_names),
        "observable_feature_names": feature_names,
        "categorical_context_features": [
            "industry",
            "site_types",
        ],
        "model_input_feature_count": len(feature_names) + 2,
        "population": {
            "test_scenarios": len(test_scenarios),
            "test_rows": len(scored_rows),
            "attack_scenarios": len(attack_scenarios),
            "benign_scenarios": len(benign_scenarios),
            "fault_scenarios": sum(
                scenario.variant == "fault"
                for scenario in test_scenarios
            ),
            "normal_scenarios": sum(
                scenario.variant == "normal"
                for scenario in test_scenarios
            ),
            "rows_per_scenario": len(WINDOWS),
            "metric_granularity": (
                "row-level; each frozen test scenario contributes "
                "one row for each 1, 5 and 15 minute window"
            ),
        },
        "overall": metric_bundle(
            labels,
            probabilities,
        ),
        "sector_slices": slice_scorecard(
            scored_rows,
            "industry",
        ),
        "site_slices": slice_scorecard(
            scored_rows,
            "site_id",
        ),
        "site_type_slices": slice_scorecard(
            scored_rows,
            "site_type",
        ),
        "zone_slices": slice_scorecard(
            scored_rows,
            "zone",
        ),
        "asset_type_slices": slice_scorecard(
            scored_rows,
            "asset_type",
        ),
        "stage_recall": build_stage_scorecards(
            model,
            attack_scenarios,
            feature_names,
        ),
        "benign_family_fpr": build_benign_family_fpr(
            model,
            benign_scenarios,
            feature_names,
        ),
        "asset_resolution": {
            "resolved_test_asset_ids": sorted(
                {
                    scenario.asset_id
                    for scenario in test_scenarios
                    if scenario.asset_id
                    in load_inventory()
                }
            ),
            "unresolved_test_asset_ids": unresolved_asset_ids,
            "unresolved_asset_rows_excluded_from_zone_site_asset_slices": sum(
                row["zone"] is None
                for row in scored_rows
            ),
            "resolution_rule": (
                "zone/site/asset_type slices use only exact asset_id "
                "matches from the canonical energy and petrochemical "
                "inventories; unresolved IDs are not assigned an invented zone"
            ),
        },
        "notes": [
            "Truth is used only for evaluation labels and slicing, never as a model input.",
            "Stage recall uses attack lifecycle stage timestamps as evaluation anchors; features remain limited to observable events at or before each anchor time.",
            "Benign-family FPR uses windows ending on/containing each benign-family event and is not an isolated-operation FPR.",
            "The 0.5 threshold is the uncalibrated RW-070-4 baseline threshold; no calibration or untouched-holdout tuning is performed in RW-070-6.",
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("RW-070-6: PASS")
    print("test_scenarios:", len(test_scenarios))
    print("test_rows:", len(scored_rows))
    print("attack_scenarios:", len(attack_scenarios))
    print("benign_scenarios:", len(benign_scenarios))
    print("observable_features:", len(feature_names))
    print("threshold:", THRESHOLD)
    print("model_sha256:", model_sha256)
    print("unresolved_test_asset_ids:", unresolved_asset_ids)
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    main()
