"""Tests for RW-140-2 retrospective Transformer evaluation."""

import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from config.ransomware.rw1402_transformer_checkpoint_evaluation import (
    compare_historical_scenarios,
    load_checkpoint,
    predict_sequence,
    summarize_predictions,
)


def sample_predictions():
    return [
        {
            "scenario_id": "attack-1",
            "variant": "attack",
            "probabilities": [0.1, 0.4, 0.8],
        },
        {
            "scenario_id": "attack-2",
            "variant": "attack",
            "probabilities": [0.1, 0.2],
        },
        {
            "scenario_id": "normal-1",
            "variant": "normal",
            "probabilities": [0.2, 0.7],
        },
    ]


def test_detection_summary():
    result = summarize_predictions(sample_predictions())

    assert result["validation_scenario_count"] == 3
    assert result["attack_scenario_count"] == 2
    assert result["detected_attack_count"] == 1
    assert result["attack_scenario_detection_rate"] == 0.5
    assert result["false_positive_scenario_count"] == 1


def test_first_threshold_crossing():
    result = summarize_predictions(sample_predictions())

    assert (
        result["scenario_results"][0][
            "first_threshold_crossing_timestep"
        ]
        == 2
    )


def test_onset_timing_unavailable():
    result = summarize_predictions(sample_predictions())

    assert result["onset_based_detection_timing_status"] == "unavailable"

    for scenario in result["scenario_results"]:
        assert scenario["verified_attack_onset_timestep"] is None
        assert scenario["onset_based_detection_delay_timesteps"] is None


def test_threshold_is_inclusive():
    predictions = [
        {
            "scenario_id": "attack-1",
            "variant": "attack",
            "probabilities": [0.5],
        }
    ]

    result = summarize_predictions(predictions)

    assert result["detected_attack_count"] == 1


@pytest.mark.parametrize("threshold", [-1, 0, 1, 2])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        summarize_predictions(sample_predictions(), threshold=threshold)


@pytest.mark.parametrize("probability", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_probability(probability):
    predictions = [
        {
            "scenario_id": "attack-1",
            "variant": "attack",
            "probabilities": [probability],
        }
    ]

    with pytest.raises(ValueError):
        summarize_predictions(predictions)


def test_empty_predictions_rejected():
    with pytest.raises(ValueError):
        summarize_predictions([])


def test_empty_probability_sequence_rejected():
    with pytest.raises(ValueError):
        summarize_predictions(
            [
                {
                    "scenario_id": "attack-1",
                    "variant": "attack",
                    "probabilities": [],
                }
            ]
        )


def test_predict_sequence_rejects_wrong_features():
    sequence = SimpleNamespace(
        timesteps=np.zeros((2, 54), dtype=np.float32)
    )

    with pytest.raises(ValueError):
        predict_sequence(None, sequence)


def test_predict_sequence_rejects_empty_sequence():
    sequence = SimpleNamespace(
        timesteps=np.zeros((0, 162), dtype=np.float32)
    )

    with pytest.raises(ValueError):
        predict_sequence(None, sequence)


def test_historical_scenario_mismatch(tmp_path):
    report_path = tmp_path / "historical.json"

    report_path.write_text(
        json.dumps(
            {
                "metrics": {
                    "scenario_results": [
                        {"scenario_id": "old-1"},
                        {"scenario_id": "shared"},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    current = [
        {"scenario_id": "shared"},
        {"scenario_id": "new-1"},
    ]

    result = compare_historical_scenarios(current, report_path)

    assert result["matching_scenario_count"] == 1
    assert result["historical_only_count"] == 1
    assert result["current_only_count"] == 1
    assert result["same_scenario_ids"] is False
    assert result["historical_performance_directly_comparable"] is False


def test_checkpoint_rejects_invalid_metadata(tmp_path):
    checkpoint_path = tmp_path / "invalid.pt"

    torch.save(
        {
            "input_features": 54,
            "window_size": 8,
            "seed": 20260921,
            "model_state_dict": {},
        },
        checkpoint_path,
    )

    with pytest.raises(ValueError, match="feature dimension"):
        load_checkpoint(checkpoint_path)
