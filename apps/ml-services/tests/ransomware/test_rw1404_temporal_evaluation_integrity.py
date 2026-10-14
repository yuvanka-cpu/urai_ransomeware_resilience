"""Tests for RW-140-4 temporal evaluation integrity audit."""

import pytest

from config.ransomware.rw1404_temporal_evaluation_integrity import (
    assignment_map,
    compare_split_provenance,
    historical_validation_ids,
)


def make_manifest(assignments):
    return {
        "scenario_count": len(assignments),
        "assignments": [
            {"scenario_id": scenario_id, "split": split}
            for scenario_id, split in assignments.items()
        ],
    }


def make_report(validation_ids):
    return {
        "validation_scenario_count": len(validation_ids),
        "metrics": {
            "scenario_results": [
                {"scenario_id": scenario_id}
                for scenario_id in validation_ids
            ]
        },
    }


@pytest.fixture
def example_data():
    historical = make_manifest({
        "attack-1": "validation",
        "attack-2": "validation",
        "benign-1": "train",
        "normal-1": "train",
        "fault-1": "test",
    })

    current = make_manifest({
        "attack-1": "validation",
        "attack-2": "train",
        "benign-1": "validation",
        "normal-1": "validation",
        "fault-1": "test",
    })

    reports = {
        "tcn": make_report(["attack-1", "attack-2"]),
        "transformer": make_report(["attack-1", "attack-2"]),
    }

    return historical, current, reports


def test_assignment_map_preserves_splits():
    manifest = make_manifest({
        "scenario-1": "train",
        "scenario-2": "validation",
    })

    assert assignment_map(manifest) == {
        "scenario-1": "train",
        "scenario-2": "validation",
    }


def test_assignment_map_rejects_duplicates():
    manifest = {
        "scenario_count": 2,
        "assignments": [
            {"scenario_id": "duplicate", "split": "train"},
            {"scenario_id": "duplicate", "split": "validation"},
        ],
    }

    with pytest.raises(ValueError, match="Duplicate"):
        assignment_map(manifest)


def test_assignment_map_rejects_count_mismatch():
    manifest = make_manifest({"scenario-1": "train"})
    manifest["scenario_count"] = 2

    with pytest.raises(ValueError, match="Scenario count"):
        assignment_map(manifest)


def test_assignment_map_rejects_non_list():
    manifest = {
        "scenario_count": 1,
        "assignments": {"scenario-1": "train"},
    }

    with pytest.raises(ValueError, match="must be a list"):
        assignment_map(manifest)


def test_historical_validation_ids_extracts_unique_ids():
    report = make_report(["attack-1", "attack-2"])

    assert historical_validation_ids(report) == {
        "attack-1",
        "attack-2",
    }


def test_historical_validation_ids_rejects_duplicates():
    report = make_report(["attack-1", "attack-1"])

    with pytest.raises(ValueError, match="Duplicate"):
        historical_validation_ids(report)


def test_historical_validation_ids_rejects_count_mismatch():
    report = make_report(["attack-1"])
    report["validation_scenario_count"] = 2

    with pytest.raises(ValueError, match="count mismatch"):
        historical_validation_ids(report)


def test_comparison_identifies_historical_training_overlap(example_data):
    historical, current, reports = example_data

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result["historical_training_overlap_count"] == 2
    assert result["historical_training_overlap_ids"] == [
        "benign-1",
        "normal-1",
    ]


def test_comparison_reports_split_distribution(example_data):
    historical, current, reports = example_data

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result[
        "historical_split_distribution_for_current_validation"
    ] == {
        "train": 2,
        "validation": 1,
    }


def test_historical_reports_match_manifest(example_data):
    historical, current, reports = example_data

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result[
        "historical_report_validation_matches_manifest"
    ] == {
        "tcn": True,
        "transformer": True,
    }

    assert result["historical_reports_share_validation_ids"] is True


def test_report_mismatch_is_detected(example_data):
    historical, current, reports = example_data

    reports["transformer"] = make_report(["attack-1"])

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result[
        "historical_report_validation_matches_manifest"
    ]["transformer"] is False

    assert result["historical_reports_share_validation_ids"] is False


def test_empty_current_validation_is_rejected(example_data):
    historical, current, reports = example_data

    for item in current["assignments"]:
        item["split"] = "train"

    with pytest.raises(ValueError, match="validation split is empty"):
        compare_split_provenance(
            historical, current, reports
        )


def test_independent_validation_is_not_claimed(example_data):
    historical, current, reports = example_data

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result["checkpoint_training_membership_verified"] is False
    assert result["independent_validation_status"] == "unverified"
    assert result["weight_level_leakage_status"] == "not_established"


def test_identical_manifests_are_recognized(example_data):
    historical, _, reports = example_data

    result = compare_split_provenance(
        historical, historical, reports
    )

    assert result["historical_manifest_matches_current"] is True
    assert result["historical_training_overlap_count"] == 0


def test_missing_historical_scenario_is_reported(example_data):
    historical, current, reports = example_data

    current["assignments"].append({
        "scenario_id": "new-1",
        "split": "validation",
    })
    current["scenario_count"] += 1

    result = compare_split_provenance(
        historical, current, reports
    )

    assert result[
        "historical_assignments_for_current_validation"
    ]["new-1"] == "absent"


def test_comparison_does_not_modify_inputs(example_data):
    import copy

    historical, current, reports = example_data

    before = copy.deepcopy((historical, current, reports))

    compare_split_provenance(
        historical, current, reports
    )

    assert (historical, current, reports) == before
