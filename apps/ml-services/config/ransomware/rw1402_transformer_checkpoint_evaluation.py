"""RW-140-2: Read-only retrospective Transformer checkpoint evaluation.

Uses the current synthetic validation split only. Does not retrain models,
write artifacts, or establish independently verified attack-onset timing.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import torch

from config.ransomware.tcn_challenger import (
    WINDOW_SIZE,
    build_sequences,
    load_and_verify_scenarios,
    pad_sequence,
)
from config.ransomware.transformer_challenger import (
    CompactTransformer,
    DETECTION_THRESHOLD,
    MODEL_PATH,
    REPORT_PATH,
    SEED,
)


def load_checkpoint(path: Path = MODEL_PATH):
    """Load trusted local weights without executing arbitrary pickle objects."""
    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=True,
    )

    if not isinstance(checkpoint, dict):
        raise ValueError("Invalid checkpoint structure")

    if checkpoint.get("input_features") != 162:
        raise ValueError("Unexpected checkpoint feature dimension")

    if checkpoint.get("window_size") != WINDOW_SIZE:
        raise ValueError("Checkpoint window-size mismatch")

    if checkpoint.get("seed") != SEED:
        raise ValueError("Checkpoint seed mismatch")

    model = CompactTransformer(checkpoint["input_features"])
    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=True,
    )
    model.eval()

    return model, checkpoint


def predict_sequence(model, sequence):
    """Generate prefix-only predictions using original Transformer preprocessing."""
    if sequence.timesteps.ndim != 2:
        raise ValueError("Expected two-dimensional timestep features")

    if sequence.timesteps.shape[1] != 162:
        raise ValueError("Unexpected sequence feature dimension")

    if len(sequence.timesteps) == 0:
        raise ValueError("Empty scenario sequence")

    probabilities = []

    model.eval()

    with torch.no_grad():
        for end in range(1, len(sequence.timesteps) + 1):
            window = pad_sequence(sequence.timesteps[:end])
            tensor = torch.from_numpy(window).unsqueeze(0)

            probability = float(
                torch.sigmoid(model(tensor)).item()
            )

            if not math.isfinite(probability):
                raise ValueError("Non-finite Transformer probability")

            probabilities.append(probability)

    return probabilities


def summarize_predictions(predictions, threshold=DETECTION_THRESHOLD):
    """Summarize scenario-level synthetic detection behavior."""
    if not 0.0 < threshold < 1.0:
        raise ValueError("Detection threshold must be between zero and one")

    if not predictions:
        raise ValueError("No validation predictions supplied")

    results = []

    for prediction in predictions:
        probabilities = prediction["probabilities"]

        if not probabilities:
            raise ValueError("Empty probability sequence")

        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for value in probabilities
        ):
            raise ValueError("Invalid probability")

        detected_at = next(
            (
                index
                for index, value in enumerate(probabilities)
                if value >= threshold
            ),
            None,
        )

        results.append(
            {
                "scenario_id": prediction["scenario_id"],
                "variant": prediction["variant"],
                "timestep_count": len(probabilities),
                "probabilities": probabilities,
                "detected": detected_at is not None,
                "first_threshold_crossing_timestep": detected_at,
                "verified_attack_onset_timestep": None,
                "onset_based_detection_delay_timesteps": None,
                "onset_based_timing_status": "unavailable",
            }
        )

    attacks = [r for r in results if r["variant"] == "attack"]
    non_attacks = [r for r in results if r["variant"] != "attack"]

    detected_attacks = sum(r["detected"] for r in attacks)
    false_positives = sum(r["detected"] for r in non_attacks)

    return {
        "validation_scenario_count": len(results),
        "variant_counts": dict(Counter(r["variant"] for r in results)),
        "attack_scenario_count": len(attacks),
        "detected_attack_count": detected_attacks,
        "attack_scenario_detection_rate": (
            detected_attacks / len(attacks) if attacks else None
        ),
        "non_attack_scenario_count": len(non_attacks),
        "false_positive_scenario_count": false_positives,
        "scenario_start_detection_delay_status": "descriptive_only",
        "onset_based_detection_timing_status": "unavailable",
        "scenario_results": results,
    }


def compare_historical_scenarios(current_results, historical_path=REPORT_PATH):
    """Identify dataset mismatch without treating historical scores as comparable."""
    historical = json.loads(
        historical_path.read_text(encoding="utf-8")
    )

    historical_results = historical["metrics"]["scenario_results"]

    historical_ids = {
        result["scenario_id"] for result in historical_results
    }
    current_ids = {
        result["scenario_id"] for result in current_results
    }

    overlap = historical_ids & current_ids

    return {
        "historical_scenario_count": len(historical_ids),
        "current_scenario_count": len(current_ids),
        "matching_scenario_count": len(overlap),
        "historical_only_count": len(historical_ids - current_ids),
        "current_only_count": len(current_ids - historical_ids),
        "same_scenario_ids": historical_ids == current_ids,
        "historical_performance_directly_comparable": False,
    }


def evaluate_checkpoint():
    """Evaluate the saved checkpoint on current validation scenarios only."""
    model, checkpoint = load_checkpoint()

    _, frozen = load_and_verify_scenarios()
    sequences = [
        sequence
        for sequence in build_sequences(frozen)
        if sequence.split == "validation"
    ]

    if not sequences:
        raise ValueError("No validation sequences available")

    predictions = []

    for sequence in sequences:
        predictions.append(
            {
                "scenario_id": sequence.scenario_id,
                "variant": sequence.variant,
                "probabilities": predict_sequence(model, sequence),
            }
        )

    summary = summarize_predictions(predictions)

    return {
        "task": "RW-140-2",
        "status": "retrospective_synthetic_validation_only",
        "model": "saved_rw0803_transformer_checkpoint",
        "checkpoint_metadata": {
            "input_features": checkpoint["input_features"],
            "window_size": checkpoint["window_size"],
            "seed": checkpoint["seed"],
        },
        "detection_threshold": DETECTION_THRESHOLD,
        "historical_dataset_comparison": compare_historical_scenarios(
            summary["scenario_results"]
        ),
        "evaluation": summary,
        "limitations": [
            "Synthetic validation scenarios only.",
            "Current validation IDs differ from historical evaluation IDs.",
            "Checkpoint provenance and original training data equivalence are not established.",
            "Historical and current performance must not be presented as directly comparable.",
            "No independently verified attack-onset annotations.",
            "First threshold crossing is not verified early ransomware detection.",
            "No operational MTTD or MTTR established.",
            "No final holdout evaluation performed.",
            "No real-world detection performance established.",
        ],
        "real_action_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_checkpoint(), indent=2))
