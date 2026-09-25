import json
from pathlib import Path


MANIFEST = Path(
    "apps/ml-services/artifacts/ransomware/offline/split_assignment_manifest.json"
)


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_untouched_holdout_ids_are_present():
    manifest = load_manifest()

    holdout = [
        item
        for item in manifest["assignments"]
        if item["split"] == "untouched_holdout"
    ]

    assert holdout
    assert all(item["scenario_id"] for item in holdout)


def test_untouched_holdout_ids_are_isolated():
    manifest = load_manifest()

    scenario_splits = {}

    for assignment in manifest["assignments"]:
        scenario_splits.setdefault(
            assignment["scenario_id"], set()
        ).add(assignment["split"])

    holdout_ids = {
        assignment["scenario_id"]
        for assignment in manifest["assignments"]
        if assignment["split"] == "untouched_holdout"
    }

    assert holdout_ids

    for scenario_id in holdout_ids:
        assert scenario_splits[scenario_id] == {"untouched_holdout"}


def test_untouched_holdout_seed_isolated():
    manifest = load_manifest()

    seed_splits = {}

    for assignment in manifest["assignments"]:
        seed_splits.setdefault(
            assignment["scenario_seed"], set()
        ).add(assignment["split"])

    holdout_seeds = {
        assignment["scenario_seed"]
        for assignment in manifest["assignments"]
        if assignment["split"] == "untouched_holdout"
    }

    assert holdout_seeds

    for seed in holdout_seeds:
        assert seed_splits[seed] == {"untouched_holdout"}


def test_manifest_declares_untouched_holdout_split():
    manifest = load_manifest()

    assert "untouched_holdout" in manifest["splits"]
    assert manifest["manifest_type"] == "split_assignment"
