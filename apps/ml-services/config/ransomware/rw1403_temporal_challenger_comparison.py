"""RW-140-3: Read-only retrospective TCN/Transformer comparison.

Uses the same current synthetic validation sequences for both checkpoints.
Does not retrain, overwrite artifacts, or evaluate the final holdout.
"""

from __future__ import annotations

import json
from collections import Counter

import torch

from config.ransomware.tcn_challenger import (
    DETECTION_THRESHOLD,
    MODEL_PATH as TCN_MODEL_PATH,
    SEED,
    TCNClassifier,
    WINDOW_SIZE,
    build_sequences,
    load_and_verify_scenarios,
)
from config.ransomware.rw1402_transformer_checkpoint_evaluation import (
    load_checkpoint as load_transformer_checkpoint,
    predict_sequence,
    summarize_predictions,
)


def load_tcn_checkpoint(path=TCN_MODEL_PATH):
    """Load the existing trusted TCN checkpoint with strict validation."""
    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=True,
    )

    if not isinstance(checkpoint, dict):
        raise ValueError("Invalid TCN checkpoint structure")

    if checkpoint.get("input_features") != 162:
        raise ValueError("Unexpected TCN feature dimension")

    if checkpoint.get("window_size") != WINDOW_SIZE:
        raise ValueError("TCN window-size mismatch")

    if checkpoint.get("seed") != SEED:
        raise ValueError("TCN seed mismatch")

    model = TCNClassifier(checkpoint["input_features"])
    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=True,
    )
    model.eval()

    return model, checkpoint


def compare_summaries(tcn_summary, transformer_summary):
    """Compare paired scenario results without ranking model quality."""
    tcn_rows = tcn_summary["scenario_results"]
    transformer_rows = transformer_summary["scenario_results"]

    tcn_ids = [row["scenario_id"] for row in tcn_rows]
    transformer_ids = [row["scenario_id"] for row in transformer_rows]

    if len(set(tcn_ids)) != len(tcn_ids):
        raise ValueError("Duplicate TCN scenario IDs")

    if len(set(transformer_ids)) != len(transformer_ids):
        raise ValueError("Duplicate Transformer scenario IDs")

    if set(tcn_ids) != set(transformer_ids):
        raise ValueError("TCN and Transformer scenario IDs differ")

    transformer_by_id = {
        row["scenario_id"]: row
        for row in transformer_rows
    }

    disagreements = []
    timing_differences = []

    for tcn_row in tcn_rows:
        transformer_row = transformer_by_id[tcn_row["scenario_id"]]

        if tcn_row["variant"] != transformer_row["variant"]:
            raise ValueError("Scenario variant mismatch")

        if tcn_row["timestep_count"] != transformer_row["timestep_count"]:
            raise ValueError("Scenario timestep-count mismatch")

        if (
            tcn_row["detected"]
            and transformer_row["detected"]
            and tcn_row["first_threshold_crossing_timestep"]
            != transformer_row["first_threshold_crossing_timestep"]
        ):
            tcn_first = tcn_row["first_threshold_crossing_timestep"]
            transformer_first = transformer_row[
                "first_threshold_crossing_timestep"
            ]

            timing_differences.append(
                {
                    "scenario_id": tcn_row["scenario_id"],
                    "variant": tcn_row["variant"],
                    "tcn_first_crossing": tcn_first,
                    "transformer_first_crossing": transformer_first,
                    "timestep_index_difference": tcn_first - transformer_first,
                }
            )

        if tcn_row["detected"] != transformer_row["detected"]:
            disagreements.append(
                {
                    "scenario_id": tcn_row["scenario_id"],
                    "variant": tcn_row["variant"],
                    "tcn_detected": tcn_row["detected"],
                    "transformer_detected": transformer_row["detected"],
                    "tcn_first_crossing": tcn_row[
                        "first_threshold_crossing_timestep"
                    ],
                    "transformer_first_crossing": transformer_row[
                        "first_threshold_crossing_timestep"
                    ],
                }
            )

    return {
        "paired_scenario_count": len(tcn_rows),
        "variant_counts": dict(
            Counter(row["variant"] for row in tcn_rows)
        ),
        "tcn_attack_detected": tcn_summary["detected_attack_count"],
        "transformer_attack_detected": transformer_summary[
            "detected_attack_count"
        ],
        "tcn_false_positive_scenarios": tcn_summary[
            "false_positive_scenario_count"
        ],
        "transformer_false_positive_scenarios": transformer_summary[
            "false_positive_scenario_count"
        ],
        "detection_disagreement_count": len(disagreements),
        "detection_disagreements": disagreements,
        "first_crossing_difference_count": len(timing_differences),
        "first_crossing_differences": timing_differences,
        "first_crossing_difference_interpretation": "scenario_relative_only",
        "verified_onset_comparison_status": "unavailable",
    }


def evaluate_challengers():
    """Evaluate both saved checkpoints on identical validation sequences."""
    tcn_model, tcn_checkpoint = load_tcn_checkpoint()
    transformer_model, transformer_checkpoint = (
        load_transformer_checkpoint()
    )

    _, frozen = load_and_verify_scenarios()

    sequences = [
        sequence
        for sequence in build_sequences(frozen)
        if sequence.split == "validation"
    ]

    if not sequences:
        raise ValueError("No validation sequences available")

    tcn_predictions = []
    transformer_predictions = []

    for sequence in sequences:
        common = {
            "scenario_id": sequence.scenario_id,
            "variant": sequence.variant,
        }

        tcn_predictions.append(
            {
                **common,
                "probabilities": predict_sequence(tcn_model, sequence),
            }
        )

        transformer_predictions.append(
            {
                **common,
                "probabilities": predict_sequence(
                    transformer_model,
                    sequence,
                ),
            }
        )

    tcn_summary = summarize_predictions(
        tcn_predictions,
        threshold=DETECTION_THRESHOLD,
    )

    transformer_summary = summarize_predictions(
        transformer_predictions,
        threshold=DETECTION_THRESHOLD,
    )

    comparison = compare_summaries(
        tcn_summary,
        transformer_summary,
    )

    return {
        "task": "RW-140-3",
        "status": "retrospective_synthetic_validation_only",
        "detection_threshold": DETECTION_THRESHOLD,
        "tcn_checkpoint": {
            "input_features": tcn_checkpoint["input_features"],
            "window_size": tcn_checkpoint["window_size"],
            "seed": tcn_checkpoint["seed"],
        },
        "transformer_checkpoint": {
            "input_features": transformer_checkpoint["input_features"],
            "window_size": transformer_checkpoint["window_size"],
            "seed": transformer_checkpoint["seed"],
        },
        "comparison": comparison,
        "tcn_evaluation": tcn_summary,
        "transformer_evaluation": transformer_summary,
        "limitations": [
            "Only current synthetic validation scenarios are evaluated.",
            "Checkpoint training-data independence is not established.",
            "Historical scenario IDs differ from current validation IDs.",
            "Historical reports are not directly comparable.",
            "First threshold crossing is not independently verified attack onset.",
            "Verified early ransomware detection is not established.",
            "No operational MTTD or MTTR is established.",
            "No final holdout evaluation is performed.",
            "No real-world model superiority or generalization is established.",
        ],
        "real_action_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_challengers(), indent=2))
