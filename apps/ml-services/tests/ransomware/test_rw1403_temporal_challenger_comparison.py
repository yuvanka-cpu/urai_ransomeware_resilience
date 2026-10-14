"""Tests for RW-140-3 retrospective temporal challenger comparison."""

import pytest
import torch

from config.ransomware.rw1402_transformer_checkpoint_evaluation import (
    summarize_predictions,
)
from config.ransomware.rw1403_temporal_challenger_comparison import (
    compare_summaries,
    load_tcn_checkpoint,
)


def make_summary(rows):
    return summarize_predictions(
        [
            {
                "scenario_id": scenario_id,
                "variant": variant,
                "probabilities": probabilities,
            }
            for scenario_id, variant, probabilities in rows
        ]
    )


def test_identical_predictions_have_no_detection_disagreements():
    rows = [
        ("attack-1", "attack", [0.2, 0.8]),
        ("normal-1", "normal", [0.1, 0.2]),
    ]

    result = compare_summaries(
        make_summary(rows),
        make_summary(rows),
    )

    assert result["paired_scenario_count"] == 2
    assert result["detection_disagreement_count"] == 0
    assert result["tcn_attack_detected"] == 1
    assert result["transformer_attack_detected"] == 1
    assert result["verified_onset_comparison_status"] == "unavailable"


def test_detection_disagreement_is_identified():
    tcn = make_summary([
        ("attack-1", "attack", [0.2, 0.8]),
        ("normal-1", "normal", [0.1, 0.2]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.2, 0.3]),
        ("normal-1", "normal", [0.1, 0.7]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["detection_disagreement_count"] == 2
    assert {
        row["scenario_id"]
        for row in result["detection_disagreements"]
    } == {"attack-1", "normal-1"}


def test_matching_ids_in_different_order_are_accepted():
    tcn = make_summary([
        ("attack-1", "attack", [0.8]),
        ("normal-1", "normal", [0.2]),
    ])

    transformer = make_summary([
        ("normal-1", "normal", [0.2]),
        ("attack-1", "attack", [0.8]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["paired_scenario_count"] == 2
    assert result["detection_disagreement_count"] == 0


def test_mismatched_scenario_ids_rejected():
    tcn = make_summary([
        ("attack-1", "attack", [0.8]),
    ])

    transformer = make_summary([
        ("attack-2", "attack", [0.8]),
    ])

    with pytest.raises(ValueError, match="scenario IDs differ"):
        compare_summaries(tcn, transformer)


def test_duplicate_tcn_ids_rejected():
    tcn = make_summary([
        ("attack-1", "attack", [0.8]),
        ("attack-1", "attack", [0.7]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.8]),
    ])

    with pytest.raises(ValueError, match="Duplicate TCN"):
        compare_summaries(tcn, transformer)


def test_duplicate_transformer_ids_rejected():
    tcn = make_summary([
        ("attack-1", "attack", [0.8]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.8]),
        ("attack-1", "attack", [0.7]),
    ])

    with pytest.raises(ValueError, match="Duplicate Transformer"):
        compare_summaries(tcn, transformer)


def test_variant_mismatch_rejected():
    tcn = make_summary([
        ("scenario-1", "attack", [0.8]),
    ])

    transformer = make_summary([
        ("scenario-1", "normal", [0.8]),
    ])

    with pytest.raises(ValueError, match="variant mismatch"):
        compare_summaries(tcn, transformer)


def test_timestep_count_mismatch_rejected():
    tcn = make_summary([
        ("attack-1", "attack", [0.2, 0.8]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.8]),
    ])

    with pytest.raises(ValueError, match="timestep-count mismatch"):
        compare_summaries(tcn, transformer)


def test_false_positive_counts_preserved():
    tcn = make_summary([
        ("attack-1", "attack", [0.8]),
        ("benign-1", "benign", [0.7]),
        ("normal-1", "normal", [0.2]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.8]),
        ("benign-1", "benign", [0.2]),
        ("normal-1", "normal", [0.9]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["tcn_false_positive_scenarios"] == 1
    assert result["transformer_false_positive_scenarios"] == 1
    assert result["detection_disagreement_count"] == 2


def test_threshold_crossing_time_difference_is_not_detection_disagreement():
    tcn = make_summary([
        ("attack-1", "attack", [0.8, 0.9]),
    ])

    transformer = make_summary([
        ("attack-1", "attack", [0.2, 0.9]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["detection_disagreement_count"] == 0
    assert result["verified_onset_comparison_status"] == "unavailable"


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("input_features", 54, "feature dimension"),
        ("window_size", 99, "window-size mismatch"),
        ("seed", 123, "seed mismatch"),
    ],
)
def test_invalid_tcn_checkpoint_metadata_rejected(
    tmp_path, field, value, error
):
    checkpoint = {
        "input_features": 162,
        "window_size": 8,
        "seed": 20260921,
        "model_state_dict": {},
    }

    checkpoint[field] = value

    path = tmp_path / "invalid_tcn.pt"
    torch.save(checkpoint, path)

    with pytest.raises(ValueError, match=error):
        load_tcn_checkpoint(path)


def test_missing_tcn_weights_rejected(tmp_path):
    path = tmp_path / "missing_weights.pt"

    torch.save(
        {
            "input_features": 162,
            "window_size": 8,
            "seed": 20260921,
            "model_state_dict": {},
        },
        path,
    )

    with pytest.raises(RuntimeError):
        load_tcn_checkpoint(path)


def test_first_crossing_difference_recorded():
    tcn = make_summary([
        ("attack-1", "attack", [0.1, 0.2, 0.8]),
    ])
    transformer = make_summary([
        ("attack-1", "attack", [0.9, 0.8, 0.7]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["detection_disagreement_count"] == 0
    assert result["first_crossing_difference_count"] == 1
    assert result["first_crossing_differences"] == [
        {
            "scenario_id": "attack-1",
            "variant": "attack",
            "tcn_first_crossing": 2,
            "transformer_first_crossing": 0,
            "timestep_index_difference": 2,
        }
    ]
    assert (
        result["first_crossing_difference_interpretation"]
        == "scenario_relative_only"
    )


def test_identical_first_crossings_not_counted():
    tcn = make_summary([
        ("attack-1", "attack", [0.2, 0.8]),
    ])
    transformer = make_summary([
        ("attack-1", "attack", [0.1, 0.9]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["first_crossing_difference_count"] == 0
    assert result["detection_disagreement_count"] == 0


def test_binary_disagreement_not_counted_as_timing_difference():
    tcn = make_summary([
        ("benign-1", "benign", [0.1, 0.2]),
    ])
    transformer = make_summary([
        ("benign-1", "benign", [0.1, 0.8]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["detection_disagreement_count"] == 1
    assert result["first_crossing_difference_count"] == 0
    assert result["first_crossing_differences"] == []


def test_reverse_timing_difference_preserves_sign():
    tcn = make_summary([
        ("attack-1", "attack", [0.9, 0.8, 0.7]),
    ])
    transformer = make_summary([
        ("attack-1", "attack", [0.1, 0.2, 0.8]),
    ])

    result = compare_summaries(tcn, transformer)

    assert result["first_crossing_difference_count"] == 1
    assert (
        result["first_crossing_differences"][0][
            "timestep_index_difference"
        ]
        == -2
    )
