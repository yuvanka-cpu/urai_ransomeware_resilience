from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from catboost import CatBoostClassifier
from sklearn.model_selection import StratifiedGroupKFold

from config.ransomware.baselines import RobustAnomalyBaseline
from config.ransomware.catboost_trainer import (
    CAT_FEATURES,
    SEED,
    WINDOWS,
    build_rows,
    class_weights,
    load_and_verify_scenarios,
    rows_to_matrix,
)
from config.ransomware.graph_propagation import load_sector_graph
from config.ransomware.rules.deterministic_rules import evaluate_rules
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)
from config.ransomware.features.window_features import extract_window_features


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "artifacts/ransomware/offline"
OUTPUT_PATH = OUTPUT_DIR / "rw0901_oof_component_scores.json"

DEVELOPMENT_SPLITS = {"train", "validation"}
N_SPLITS = 3


def _event_time(event) -> datetime:
    return datetime.fromisoformat(event.event_time.replace("Z", "+00:00"))


def _window_events(events, end_time: datetime, minutes: int):
    start = end_time - timedelta(minutes=minutes)
    return [
        event
        for event in events
        if start <= _event_time(event) <= end_time
    ]


def _rule_score(features: dict[str, float | int]) -> float:
    evidence = evaluate_rules(features)
    triggered = sum(int(item.triggered) for item in evidence)
    return round(triggered / len(evidence), 6)


def _anomaly_score(evidence) -> float:
    candidates = [
        float(evidence.univariate_evidence_count),
        (
            float(evidence.multivariate_score)
            / float(evidence.multivariate_threshold)
            if evidence.multivariate_threshold > 0
            else 0.0
        ),
        1.0 if evidence.isolation_triggered else 0.0,
    ]
    return round(max(0.0, min(1.0, max(candidates))), 6)


def _graph_score(
    sector: str,
    events,
    end_time: datetime,
    window_minutes: int,
) -> tuple[float, int]:
    graph = load_sector_graph(sector)
    window = _window_events(events, end_time, window_minutes)

    seed_assets = sorted(
        {
            event.asset_id
            for event in window
            if event.asset_id in graph.assets
        }
    )

    if not seed_assets:
        return 0.0, 0

    propagated = graph.propagate(seed_assets)

    # Seeds themselves are evidence already observed. The fusion component
    # represents additional graph-exposed assets only.
    exposed = [
        result
        for result in propagated
        if result.asset_id not in set(seed_assets)
    ]

    if not exposed:
        return 0.0, 0

    return round(max(result.score for result in exposed), 6), len(exposed)


def _make_catboost(
    feature_names: list[str],
    train_rows,
) -> CatBoostClassifier:
    labels = [row.label for row in train_rows]
    weights = class_weights(labels)
    cat_indices = [
        len(feature_names) + index
        for index, _ in enumerate(CAT_FEATURES)
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
        rows_to_matrix(train_rows, feature_names),
        [row.label for row in train_rows],
    )
    return model


def _build_anomaly(
    feature_names: list[str],
    train_rows,
) -> RobustAnomalyBaseline:
    baseline = RobustAnomalyBaseline(
        feature_names,
        random_state=SEED,
    )
    baseline.fit(
        row.features
        for row in train_rows
    )
    return baseline


def _scenario_metadata(frozen):
    return {
        scenario.scenario_id: scenario
        for scenario in frozen
        if scenario.split in DEVELOPMENT_SPLITS
    }


def generate_oof():
    manifest, frozen = load_and_verify_scenarios()

    development = [
        scenario
        for scenario in frozen
        if scenario.split in DEVELOPMENT_SPLITS
    ]

    if not development:
        raise ValueError("No development scenarios available")

    scenario_labels = [1 if s.variant == "attack" else 0 for s in development]
    scenario_groups = [s.scenario_id for s in development]

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=SEED,
    )

    rows, feature_names = build_rows(frozen)

    rows_by_scenario = {}
    for row in rows:
        if row.split in DEVELOPMENT_SPLITS:
            rows_by_scenario.setdefault(row.scenario_id, []).append(row)

    scenario_by_id = _scenario_metadata(frozen)

    oof = []

    for fold, (train_idx, score_idx) in enumerate(
        splitter.split(
            development,
            scenario_labels,
            groups=scenario_groups,
        ),
        start=1,
    ):
        train_scenarios = [development[index] for index in train_idx]
        score_scenarios = [development[index] for index in score_idx]

        train_ids = {scenario.scenario_id for scenario in train_scenarios}
        score_ids = {scenario.scenario_id for scenario in score_scenarios}

        if train_ids & score_ids:
            raise AssertionError("Scenario leakage detected between OOF folds")

        train_rows = [
            row
            for row in rows
            if row.scenario_id in train_ids
        ]

        score_rows = [
            row
            for row in rows
            if row.scenario_id in score_ids
        ]

        catboost = _make_catboost(feature_names, train_rows)
        anomaly = _build_anomaly(feature_names, train_rows)

        cat_matrix = rows_to_matrix(score_rows, feature_names)
        cat_probabilities = catboost.predict_proba(cat_matrix)[:, 1]

        for row, cat_probability in zip(score_rows, cat_probabilities):
            scenario = scenario_by_id[row.scenario_id]
            events = assemble_scenario_events(scenario)
            end_time = datetime.fromisoformat(
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

            oof.append(
                {
                    "fold": fold,
                    "scenario_id": row.scenario_id,
                    "industry": row.industry,
                    "split": row.split,
                    "window_minutes": row.window_minutes,
                    "label": row.label,
                    "rule_score": rule_score,
                    "anomaly_score": anomaly_score,
                    "catboost_score": round(float(cat_probability), 6),
                    "temporal_score": None,
                    "temporal_status": "unavailable_rejected_challenger",
                    "graph_score": graph_score,
                    "graph_exposed_asset_count": graph_exposed_count,
                    "graph_status": "deterministic_weighted_propagation",
                }
            )

    oof.sort(
        key=lambda item: (
            item["scenario_id"],
            item["window_minutes"],
        )
    )

    scenario_ids = {item["scenario_id"] for item in oof}

    expected_ids = {scenario.scenario_id for scenario in development}

    if scenario_ids != expected_ids:
        missing = sorted(expected_ids - scenario_ids)
        extra = sorted(scenario_ids - expected_ids)
        raise AssertionError(
            f"OOF scenario coverage mismatch; missing={missing}, extra={extra}"
        )

    if any(item["split"] not in DEVELOPMENT_SPLITS for item in oof):
        raise AssertionError("Non-development scenario entered OOF table")

    if len(oof) != len(development) * len(WINDOWS):
        raise AssertionError(
            f"Expected {len(development) * len(WINDOWS)} OOF rows, "
            f"found {len(oof)}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "task": "RW-090-1",
        "description": (
            "Out-of-fold component scores generated only from training/"
            "development scenarios."
        ),
        "synthetic_only": True,
        "seed": SEED,
        "development_splits": sorted(DEVELOPMENT_SPLITS),
        "excluded_splits": [
            "calibration",
            "test",
            "untouched_holdout",
        ],
        "scenario_count": len(development),
        "row_count": len(oof),
        "window_minutes": list(WINDOWS),
        "feature_count": len(feature_names),
        "component_contract": {
            "rules": "deterministic evidence ratio",
            "anomaly": "fold-fitted robust anomaly evidence",
            "catboost": "fold-fitted CatBoost probability",
            "temporal": "unavailable_rejected_challenger",
            "graph": "deterministic weighted propagation",
        },
        "leakage_controls": {
            "scenario_grouped_oof": True,
            "holdout_rows_present": False,
            "calibration_rows_present": False,
            "truth_used_as_feature": False,
            "future_fields_used": False,
        },
        "source_manifest": str(
            MANIFEST_PATH.relative_to(ROOT)
        ) if "MANIFEST_PATH" in globals() else (
            "artifacts/ransomware/offline/split_assignment_manifest.json"
        ),
        "rows": oof,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(f"RW-090-1 wrote: {OUTPUT_PATH}")
    print(f"Development scenarios: {len(development)}")
    print(f"OOF rows: {len(oof)}")
    print("Holdout/calibration rows: 0")
    print("Temporal component: unavailable (rejected challenger)")
    print("Graph component: deterministic weighted propagation")


if __name__ == "__main__":
    generate_oof()
