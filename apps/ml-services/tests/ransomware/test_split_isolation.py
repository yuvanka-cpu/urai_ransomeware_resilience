import json
from collections import defaultdict
from pathlib import Path


MANIFEST_PATH = Path(
    "apps/ml-services/artifacts/ransomware/offline/"
    "split_assignment_manifest.json"
)


def load_manifest():
    return json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )


def test_scenario_ids_do_not_cross_splits():
    manifest = load_manifest()
    assignments = manifest["assignments"]

    scenario_splits = defaultdict(set)

    for assignment in assignments:
        scenario_splits[
            assignment["scenario_id"]
        ].add(assignment["split"])

    leaking_scenarios = {
        scenario_id: sorted(splits)
        for scenario_id, splits in scenario_splits.items()
        if len(splits) > 1
    }

    assert leaking_scenarios == {}


def test_each_scenario_has_exactly_one_split():
    manifest = load_manifest()

    scenario_splits = defaultdict(set)

    for assignment in manifest["assignments"]:
        scenario_splits[
            assignment["scenario_id"]
        ].add(assignment["split"])

    assert scenario_splits
    assert all(
        len(splits) == 1
        for splits in scenario_splits.values()
    )


def test_scenario_seed_does_not_cross_splits():
    manifest = load_manifest()

    seed_splits = defaultdict(set)

    for assignment in manifest["assignments"]:
        seed_splits[
            assignment["scenario_seed"]
        ].add(assignment["split"])

    leaking_seeds = {
        seed: sorted(splits)
        for seed, splits in seed_splits.items()
        if len(splits) > 1
    }

    assert leaking_seeds == {}


def test_same_scenario_identity_is_not_repeated():
    manifest = load_manifest()

    identities = [
        (
            assignment["scenario_id"],
            assignment["scenario_seed"],
        )
        for assignment in manifest["assignments"]
    ]

    assert len(identities) == len(set(identities))


def test_manifest_records_isolation_scope():
    manifest = load_manifest()

    assert manifest["manifest_type"] == "split_assignment"

    required_fields = {
        "scenario_id",
        "scenario_seed",
        "use_case_id",
        "industry",
        "variant",
        "asset_id",
        "split",
    }

    for assignment in manifest["assignments"]:
        assert required_fields.issubset(assignment)
        