import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "artifacts"
    / "ransomware"
    / "offline"
    / "rw0907_rejected_candidate_registry.json"
)


EXPECTED = {
    "tcn",
    "compact_transformer",
    "graphsage",
    "gatv2",
}


def test_rw0907_registry_contract():
    assert REGISTRY.is_file()

    registry = json.loads(
        REGISTRY.read_text(encoding="utf-8")
    )

    assert registry["task"] == "RW-090-7"
    assert registry["artifact_type"] == "rejected_candidate_registry"
    assert registry["synthetic_only"] is True

    boundary = registry["promotion_boundary"]

    assert boundary["final_decision"] == "NO_CHALLENGER_PROMOTED"
    assert boundary["rejected_candidate_count"] == 4
    assert boundary["all_rejected_candidates_recorded"] is True

    candidates = registry["candidates"]

    assert len(candidates) == 4
    assert {
        candidate["candidate"]
        for candidate in candidates
    } == EXPECTED

    assert all(
        candidate["promotion_status"] == "REJECT"
        for candidate in candidates
    )

    assert all(
        candidate["reason"]
        for candidate in candidates
    )

    assert all(
        candidate["source_task"] == "RW-080-7"
        for candidate in candidates
    )


def test_rw0907_retains_graph_baseline_separately():
    registry = json.loads(
        REGISTRY.read_text(encoding="utf-8")
    )

    baseline = registry["retained_auditable_baseline"]

    assert baseline["component"] == (
        "deterministic_weighted_graph_propagation"
    )
    assert baseline["status"] == "retained_baseline"


def test_rw0907_safety_and_promotion_contract():
    registry = json.loads(
        REGISTRY.read_text(encoding="utf-8")
    )

    contract = registry["contract"]

    assert contract["promotion_by_novelty_forbidden"] is True
    assert contract["promotion_by_pool_accuracy_forbidden"] is True
    assert contract["final_holdout_used"] is False
    assert contract["calibration_evidence_required"] is True
    assert contract["runtime_evidence_required"] is True
    assert contract["human_approval_required"] is True
    assert contract["real_action_executed"] is False
    assert contract["operational_state_claimed"] is False
