import json
from pathlib import Path


ARTIFACT = Path(
    "artifacts/ransomware/offline/rw0807_promotion_decision.json"
)


def test_rw0807_rejects_unproven_complexity():
    assert ARTIFACT.exists()

    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert report["task"] == "RW-080-7"
    assert report["status"] == "PASS"
    assert report["decision"] == "NO_CHALLENGER_PROMOTED"
    assert report["synthetic_only"] is True
    assert report["real_action_executed"] is False
    assert report["final_holdout_used"] is False

    expected = {"tcn", "compact_transformer", "graphsage", "gatv2"}

    assert set(report["decisions"]) == expected
    assert all(
        report["decisions"][name]["promotion"] == "REJECT"
        for name in expected
    )

    thresholds = report["predeclared_thresholds"]

    assert thresholds["temporal_detection_delay_improvement_timesteps"] == 2.0
    assert thresholds["temporal_stage_recall_improvement_absolute"] == 0.10
    assert thresholds["graph_weighted_overlap_improvement_absolute"] == 0.10
