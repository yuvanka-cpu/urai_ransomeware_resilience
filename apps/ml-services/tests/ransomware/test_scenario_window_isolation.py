from __future__ import annotations

import json
from pathlib import Path

from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
    sequence_fingerprint,
)
from config.ransomware.scenarios.scenario_registry import (
    FrozenScenario,
)


BASE_SEED = 20260921
MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "ransomware"
    / "offline"
    / "split_assignment_manifest.json"
)


def _scenarios() -> list[FrozenScenario]:
    manifest = json.loads(MANIFEST_PATH.read_text())

    assert manifest["base_seed"] == BASE_SEED
    assert manifest["scenario_count"] == len(manifest["assignments"])

    return [
        FrozenScenario(**assignment)
        for assignment in manifest["assignments"]
    ]


def test_scenario_ids_do_not_cross_splits():
    scenarios = _scenarios()
    by_id = {}

    for scenario in scenarios:
        by_id.setdefault(scenario.scenario_id, set()).add(scenario.split)

    assert all(len(splits) == 1 for splits in by_id.values())


def test_scenario_seeds_do_not_cross_splits():
    scenarios = _scenarios()
    by_seed = {}

    for scenario in scenarios:
        by_seed.setdefault(scenario.scenario_seed, set()).add(scenario.split)

    assert all(len(splits) == 1 for splits in by_seed.values())


def test_scenario_id_and_seed_pairs_are_unique():
    scenarios = _scenarios()
    identities = [
        (scenario.scenario_id, scenario.scenario_seed)
        for scenario in scenarios
    ]

    assert len(identities) == len(set(identities))


def test_each_scenario_has_one_complete_event_sequence():
    scenarios = _scenarios()

    for scenario in scenarios:
        events = assemble_scenario_events(scenario)

        assert events
        assert all(event.scenario_id == scenario.scenario_id for event in events)
        assert all(event.scenario_seed == scenario.scenario_seed for event in events)
        assert all(event.split == scenario.split for event in events)
        assert [event.sequence_index for event in events] == list(range(len(events)))


def test_sequence_fingerprints_do_not_cross_splits():
    scenarios = _scenarios()
    fingerprints_by_split = {}

    for scenario in scenarios:
        fingerprint = sequence_fingerprint(
            assemble_scenario_events(scenario)
        )
        fingerprints_by_split.setdefault(fingerprint, set()).add(
            scenario.split
        )

    assert all(
        len(splits) == 1
        for splits in fingerprints_by_split.values()
    )


def test_rw_050_4_graph_variant_scope_is_explicit():
    evidence = {
        "asset_graph_variant_overlap": "not_assessable",
        "reason": (
            "The current repository contains static sector graph files, "
            "not scenario-specific graph variants. The graph contract "
            "defines canonical edge types but does not define graph-variant "
            "identifiers or fingerprints."
        ),
    }

    assert evidence["asset_graph_variant_overlap"] == "not_assessable"
