from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from config.ransomware.rw0901_oof_scores import generate_oof
from config.ransomware.rw0903_sector_calibration import (
    apply_sigmoid,
    build_stacking_probability,
)


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "ransomware" / "offline"
MODEL_DIR = ROOT / "artifacts" / "ransomware" / "models"

OOF_REPORT = ARTIFACT_DIR / "rw0901_oof_component_scores.json"
STACKING_MODEL = MODEL_DIR / "rw0902_logistic_stacking_model.json"
CALIBRATOR = MODEL_DIR / "rw0903_sector_calibrators.json"
REPORT = ARTIFACT_DIR / "rw0904_threshold_policy_report.json"

SEED = 20260921

# Declared operational cost policy.
# These are policy assumptions, not learned parameters.
COSTS = {
    "attack_classified_normal": 10.0,
    "attack_classified_investigate": 6.0,
    "benign_classified_investigate": 1.0,
    "benign_classified_high_risk": 4.0,
}


def _load_artifacts() -> tuple[list[dict], dict, dict]:
    # RW-090-1 writes the frozen OOF artifact.
    generate_oof()

    oof_payload = json.loads(
        OOF_REPORT.read_text(encoding="utf-8")
    )
    stacking_model_payload = json.loads(
        STACKING_MODEL.read_text(encoding="utf-8")
    )
    calibrator_payload = json.loads(
        CALIBRATOR.read_text(encoding="utf-8")
    )

    rows = oof_payload["rows"]

    observed_splits = {row["split"] for row in rows}

    if observed_splits != {"train", "validation"}:
        raise AssertionError(
            "RW-090-4 requires only development OOF rows; "
            f"got {sorted(observed_splits)}"
        )

    forbidden = {"calibration", "test", "untouched_holdout"}
    if observed_splits & forbidden:
        raise AssertionError(
            f"Forbidden split present: "
            f"{sorted(observed_splits & forbidden)}"
        )

    return rows, stacking_model_payload, calibrator_payload


def _calibrated_rows(
    rows: list[dict],
    stacking_model_payload: dict,
    calibrator_payload: dict,
) -> list[dict]:
    calibrated = []

    for row in rows:
        raw_probability = build_stacking_probability(
            stacking_model_payload,
            rule_score=float(row["rule_score"]),
            anomaly_score=float(row["anomaly_score"]),
            catboost_score=float(row["catboost_score"]),
            graph_score=float(row["graph_score"]),
        )

        sector = row["industry"]
        sector_entry = calibrator_payload["sector_calibrators"][sector]

        if sector_entry["status"] == "sector_specific":
            # RW-090-3 stores sigmoid parameters directly in the
            # sector entry.
            calibrator = sector_entry
            calibration_status = "sector_specific"

        elif sector_entry["status"] == "insufficient_class_diversity":
            # RW-090-3 explicitly declares global sigmoid fallback.
            if sector_entry.get("fallback") != "global_sigmoid":
                raise AssertionError(
                    f"Unexpected fallback contract for {sector}"
                )

            calibrator = calibrator_payload["global_calibrator"]
            calibration_status = "global_fallback"

        else:
            raise AssertionError(
                f"Unexpected sector calibration status for {sector}: "
                f"{sector_entry['status']}"
            )

        probability = float(
            apply_sigmoid(
                calibrator,
                np.asarray([raw_probability], dtype=float),
            )[0]
        )

        calibrated.append(
            {
                "scenario_id": row["scenario_id"],
                "split": row["split"],
                "industry": sector,
                "window_minutes": row["window_minutes"],
                "label": int(row["label"]),
                "raw_stacking_probability": raw_probability,
                "calibrated_probability": probability,
                "calibration_status": calibration_status,
            }
        )

    return calibrated


def _scenario_rows(rows: list[dict]) -> list[dict]:
    """
    Collapse the three operational windows into one scenario-level value.

    The maximum calibrated probability is retained so that an attack signal
    appearing in any declared observation window is not diluted by averaging.
    """
    scenarios: dict[str, dict] = {}

    for row in rows:
        current = scenarios.get(row["scenario_id"])
        candidate = dict(row)

        if (
            current is None
            or candidate["calibrated_probability"]
            > current["calibrated_probability"]
        ):
            scenarios[row["scenario_id"]] = candidate

    return sorted(
        scenarios.values(),
        key=lambda item: item["scenario_id"],
    )


def _observed_threshold_candidates(rows: list[dict]) -> tuple[float, ...]:
    """
    Generate threshold candidates from the calibrated score scale actually
    observed in development OOF scenarios.

    This avoids imposing an arbitrary probability convention such as 0.50
    when the calibrated model's observed output range is materially lower.

    Only development OOF evidence is used here.
    """
    scenarios = _scenario_rows(rows)

    observed = sorted(
        {
            round(float(row["calibrated_probability"]), 6)
            for row in scenarios
        }
    )

    if len(observed) < 2:
        raise RuntimeError(
            "RW-090-4 requires at least two distinct scenario-level "
            "calibrated probabilities."
        )

    return tuple(observed)


def _decision(
    probability: float,
    investigate: float,
    high_risk: float,
) -> str:
    if probability >= high_risk:
        return "high_risk"

    if probability >= investigate:
        return "investigate"

    return "normal"


def _evaluate(
    rows: list[dict],
    investigate: float,
    high_risk: float,
) -> dict:
    scenarios = _scenario_rows(rows)

    normal_attack = 0
    investigate_attack = 0
    investigate_benign = 0
    high_risk_benign = 0
    high_risk_attack = 0
    normal_benign = 0

    for row in scenarios:
        decision = _decision(
            row["calibrated_probability"],
            investigate,
            high_risk,
        )

        if row["label"] == 1:
            if decision == "normal":
                normal_attack += 1
            elif decision == "investigate":
                investigate_attack += 1
            else:
                high_risk_attack += 1

        else:
            if decision == "normal":
                normal_benign += 1
            elif decision == "investigate":
                investigate_benign += 1
            else:
                high_risk_benign += 1

    total_cost = (
        normal_attack * COSTS["attack_classified_normal"]
        + investigate_attack * COSTS["attack_classified_investigate"]
        + investigate_benign * COSTS["benign_classified_investigate"]
        + high_risk_benign * COSTS["benign_classified_high_risk"]
    )

    attack_count = sum(
        row["label"] == 1
        for row in scenarios
    )

    benign_count = sum(
        row["label"] == 0
        for row in scenarios
    )

    return {
        "scenario_count": len(scenarios),
        "attack_count": attack_count,
        "benign_count": benign_count,
        "normal_attack": normal_attack,
        "investigate_attack": investigate_attack,
        "high_risk_attack": high_risk_attack,
        "normal_benign": normal_benign,
        "investigate_benign": investigate_benign,
        "high_risk_benign": high_risk_benign,
        "high_risk_recall": (
            high_risk_attack / attack_count
            if attack_count
            else 0.0
        ),
        "investigate_or_higher_recall": (
            (investigate_attack + high_risk_attack) / attack_count
            if attack_count
            else 0.0
        ),
        "false_positive_rate": (
            (investigate_benign + high_risk_benign) / benign_count
            if benign_count
            else 0.0
        ),
        "total_cost": round(float(total_cost), 6),
    }


def _select_thresholds(
    rows: list[dict],
) -> tuple[float, float, dict]:
    threshold_candidates = _observed_threshold_candidates(rows)
    candidates = []

    for investigate in threshold_candidates:
        for high_risk in threshold_candidates:
            if high_risk <= investigate:
                continue

            metrics = _evaluate(
                rows,
                investigate=investigate,
                high_risk=high_risk,
            )

            # A high-risk threshold must identify at least one attack.
            # This prevents a meaningless high-risk band that is never used.
            if metrics["high_risk_attack"] < 1:
                continue

            candidates.append(
                {
                    "investigate_threshold": investigate,
                    "high_risk_threshold": high_risk,
                    **metrics,
                }
            )

    if not candidates:
        raise RuntimeError(
            "No eligible threshold pair found. "
            "No candidate high-risk threshold identifies an attack."
        )

    # Primary criterion:
    #   minimum declared operational cost.
    #
    # Tie-breakers:
    #   1. higher high-risk recall
    #   2. higher high-risk threshold
    #   3. higher investigate threshold
    #
    # This keeps the threshold decision deterministic and auditable.
    selected = min(
        candidates,
        key=lambda item: (
            item["total_cost"],
            -item["high_risk_recall"],
            -item["high_risk_threshold"],
            -item["investigate_threshold"],
        ),
    )

    return (
        float(selected["investigate_threshold"]),
        float(selected["high_risk_threshold"]),
        {
            "candidate_count": len(candidates),
            "threshold_candidates": [
                float(value)
                for value in threshold_candidates
            ],
            "selected": selected,
            "all_eligible_candidates": candidates,
        },
    )


def _sensitivity_analysis(
    rows: list[dict],
    investigate: float,
    high_risk: float,
) -> list[dict]:
    """
    Evaluate fixed threshold perturbations on development OOF evidence.

    This is sensitivity analysis only; it does not retune the thresholds.
    """
    results = []

    perturbations = (
        ("minus_0_10", -0.10),
        ("minus_0_05", -0.05),
        ("selected", 0.00),
        ("plus_0_05", 0.05),
        ("plus_0_10", 0.10),
    )

    for label, delta in perturbations:
        adjusted_investigate = investigate + delta
        adjusted_high_risk = high_risk + delta

        # Preserve the required ordering of the decision bands.
        if adjusted_high_risk <= adjusted_investigate:
            continue

        metrics = _evaluate(
            rows,
            investigate=adjusted_investigate,
            high_risk=adjusted_high_risk,
        )

        results.append(
            {
                "label": label,
                "delta": delta,
                "investigate_threshold": round(
                    adjusted_investigate,
                    6,
                ),
                "high_risk_threshold": round(
                    adjusted_high_risk,
                    6,
                ),
                **metrics,
            }
        )

    return results


def _score_overlap_summary(rows: list[dict]) -> dict:
    scenarios = _scenario_rows(rows)

    attacks = [
        float(row["calibrated_probability"])
        for row in scenarios
        if row["label"] == 1
    ]

    benign = [
        float(row["calibrated_probability"])
        for row in scenarios
        if row["label"] == 0
    ]

    if not attacks or not benign:
        return {
            "attack_score_range": None,
            "benign_score_range": None,
            "score_overlap_observed": None,
        }

    attack_min = min(attacks)
    attack_max = max(attacks)
    benign_min = min(benign)
    benign_max = max(benign)

    overlap = not (
        attack_max < benign_min
        or benign_max < attack_min
    )

    return {
        "attack_score_range": {
            "min": round(attack_min, 6),
            "max": round(attack_max, 6),
        },
        "benign_score_range": {
            "min": round(benign_min, 6),
            "max": round(benign_max, 6),
        },
        "score_overlap_observed": overlap,
    }


def build_report(
    rows: list[dict],
    investigate: float,
    high_risk: float,
    selection: dict,
    sensitivity: list[dict],
) -> dict:
    scenarios = _scenario_rows(rows)

    split_counts: dict[str, int] = {}

    for row in rows:
        split_counts[row["split"]] = (
            split_counts.get(row["split"], 0) + 1
        )

    sector_counts: dict[str, int] = {}

    for row in scenarios:
        sector_counts[row["industry"]] = (
            sector_counts.get(row["industry"], 0) + 1
        )

    return {
        "task": "RW-090-4",
        "synthetic_only": True,
        "seed": SEED,
        "threshold_policy": {
            "investigate_threshold": investigate,
            "high_risk_threshold": high_risk,
            "candidate_policy": (
                "observed_development_scenario_scores"
            ),
            "scenario_aggregation": "maximum_calibrated_probability",
            "decision_order": [
                "high_risk",
                "investigate",
                "normal",
            ],
        },
        "declared_cost_policy": COSTS,
        "training_scope": {
            "threshold_selection_split": [
                "train",
                "validation",
            ],
            "development_oof_only": True,
            "calibration_split_used": False,
            "test_split_used": False,
            "final_holdout_used": False,
            "thresholds_frozen_before_final_holdout": True,
        },
        "data_summary": {
            "oof_row_count": len(rows),
            "scenario_count": len(scenarios),
            "split_row_counts": split_counts,
            "sector_scenario_counts": sector_counts,
        },
        "score_overlap": _score_overlap_summary(rows),
        "selection": selection,
        "sensitivity_analysis": sensitivity,
        "contract": {
            "no_final_holdout_tuning": True,
            "no_test_tuning": True,
            "no_calibration_tuning": True,
            "unavailable_behavior_deferred_to_rw0905": True,
            "human_approval_required": True,
            "real_action_executed": False,
            "physical_safety_determination": "not_determined",
            "operational_state_claimed": False,
        },
    }


def main() -> None:
    rows, stacking_model_payload, calibrator_payload = _load_artifacts()

    calibrated_rows = _calibrated_rows(
        rows,
        stacking_model_payload,
        calibrator_payload,
    )

    investigate, high_risk, selection = _select_thresholds(
        calibrated_rows
    )

    sensitivity = _sensitivity_analysis(
        calibrated_rows,
        investigate=investigate,
        high_risk=high_risk,
    )

    report = build_report(
        calibrated_rows,
        investigate=investigate,
        high_risk=high_risk,
        selection=selection,
        sensitivity=sensitivity,
    )

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    selected = selection["selected"]

    print("=== RW-090-4 COMPLETE ===")
    print(
        f"Development scenarios: "
        f"{selected['scenario_count']}"
    )
    print(
        f"Investigate threshold: "
        f"{investigate:.6f}"
    )
    print(
        f"High-risk threshold: "
        f"{high_risk:.6f}"
    )
    print(
        f"Total declared cost: "
        f"{selected['total_cost']:.2f}"
    )
    print(
        f"High-risk recall: "
        f"{selected['high_risk_recall']:.4f}"
    )
    print(
        f"Investigate-or-higher recall: "
        f"{selected['investigate_or_higher_recall']:.4f}"
    )
    print(
        f"False-positive rate: "
        f"{selected['false_positive_rate']:.4f}"
    )
    print(
        f"Score overlap observed: "
        f"{report['score_overlap']['score_overlap_observed']}"
    )
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
