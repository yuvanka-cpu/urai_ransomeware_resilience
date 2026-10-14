"""Tests for RW-140-1 offline temporal evaluation audit."""

import pytest

from config.ransomware.rw1401_temporal_evaluation_audit import (
    evaluate_temporal_detection,
)


def test_detection_at_onset():
    result = evaluate_temporal_detection(
        [0.1, 0.2, 0.8, 0.9],
        onset_index=2,
    )
    assert result["status"] == "available"
    assert result["first_alert_index"] == 2
    assert result["post_onset_detection_delay_timesteps"] == 0


def test_detection_after_onset():
    result = evaluate_temporal_detection(
        [0.1, 0.2, 0.3, 0.8],
        onset_index=1,
    )
    assert result["first_post_onset_alert_index"] == 3
    assert result["post_onset_detection_delay_timesteps"] == 2


def test_pre_onset_alert_is_separate():
    result = evaluate_temporal_detection(
        [0.8, 0.2, 0.3, 0.9],
        onset_index=2,
    )
    assert result["first_alert_index"] == 0
    assert result["pre_onset_alert_indices"] == [0]
    assert result["first_post_onset_alert_index"] == 3
    assert result["post_onset_detection_delay_timesteps"] == 1


def test_only_pre_onset_alerts():
    result = evaluate_temporal_detection(
        [0.9, 0.1, 0.1],
        onset_index=2,
    )
    assert result["pre_onset_alert_count"] == 1
    assert result["post_onset_detected"] is False
    assert result["post_onset_detection_delay_timesteps"] is None


def test_no_alerts():
    result = evaluate_temporal_detection(
        [0.1, 0.2, 0.3],
        onset_index=1,
    )
    assert result["first_alert_index"] is None
    assert result["post_onset_detected"] is False


def test_onset_at_first_timestep():
    result = evaluate_temporal_detection(
        [0.8, 0.9],
        onset_index=0,
    )
    assert result["pre_onset_alert_count"] == 0
    assert result["post_onset_detection_delay_timesteps"] == 0


def test_threshold_boundary_is_inclusive():
    result = evaluate_temporal_detection(
        [0.2, 0.5],
        onset_index=1,
        threshold=0.5,
    )
    assert result["first_alert_index"] == 1


@pytest.mark.parametrize("probabilities", [
    [],
    None,
    "0.8",
    [float("nan")],
    [float("inf")],
    [-0.1],
    [1.1],
    [True],
    ["0.8"],
])
def test_invalid_probabilities_unavailable(probabilities):
    result = evaluate_temporal_detection(
        probabilities,
        onset_index=0,
    )
    assert result["status"] == "unavailable"


@pytest.mark.parametrize("onset", [
    None,
    True,
    -1,
    3,
    1.5,
    "1",
])
def test_invalid_onset_unavailable(onset):
    result = evaluate_temporal_detection(
        [0.1, 0.8, 0.9],
        onset_index=onset,
    )
    assert result["status"] == "unavailable"


@pytest.mark.parametrize("threshold", [
    0,
    -0.1,
    1.1,
    float("nan"),
    float("inf"),
    True,
    "0.5",
])
def test_invalid_threshold_unavailable(threshold):
    result = evaluate_temporal_detection(
        [0.1, 0.8],
        onset_index=1,
        threshold=threshold,
    )
    assert result["status"] == "unavailable"


def test_no_operational_mttd_claim():
    result = evaluate_temporal_detection(
        [0.1, 0.9],
        onset_index=0,
    )
    assert "not operational minutes or MTTD" in result["limitations"]


def test_missing_onset_never_defaults_to_zero():
    result = evaluate_temporal_detection(
        [0.9, 0.9],
        onset_index=None,
    )
    assert result["status"] == "unavailable"
    assert "post_onset_detection_delay_timesteps" not in result
