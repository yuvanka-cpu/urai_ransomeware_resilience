"""RW-140-4: Read-only temporal model evaluation integrity audit.

Compares historical checkpoint-commit split assignments with the current
synthetic validation split. Does not load model weights, retrain, or access
the frozen final holdout.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

from config.ransomware.catboost_trainer import MANIFEST_PATH

CHECKPOINT_COMMIT = "6c847c5"

RELATIVE_MANIFEST_PATH = (
    "apps/ml-services/artifacts/ransomware/offline/"
    "split_assignment_manifest.json"
)

REPORT_DIR = MANIFEST_PATH.parent

HISTORICAL_REPORTS = {
    "tcn": "rw0802_tcn_report.json",
    "transformer": "rw0803_transformer_report.json",
}


def load_historical_manifest(
    commit: str = CHECKPOINT_COMMIT,
) -> dict:
    """Read a committed manifest without modifying the working tree."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{RELATIVE_MANIFEST_PATH}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def assignment_map(manifest: dict) -> dict[str, str]:
    """Validate and index scenario-to-split assignments."""
    assignments = manifest["assignments"]

    if not isinstance(assignments, list):
        raise ValueError("Manifest assignments must be a list")

    result = {}

    for item in assignments:
        scenario_id = item["scenario_id"]
        split = item["split"]

        if scenario_id in result:
            raise ValueError(
                f"Duplicate scenario assignment: {scenario_id}"
            )

        result[scenario_id] = split

    if len(result) != manifest["scenario_count"]:
        raise ValueError("Scenario count does not match assignments")

    return result


def historical_validation_ids(report: dict) -> set[str]:
    """Extract historical validation IDs from scenario-level records."""
    rows = report["metrics"]["scenario_results"]
    ids = [row["scenario_id"] for row in rows]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate historical validation scenario IDs")

    if len(ids) != report["validation_scenario_count"]:
        raise ValueError("Historical validation count mismatch")

    return set(ids)


def compare_split_provenance(
    historical_manifest: dict,
    current_manifest: dict,
    historical_reports: dict[str, dict],
) -> dict:
    """Compare recorded assignments without claiming weight-level leakage."""
    historical = assignment_map(historical_manifest)
    current = assignment_map(current_manifest)

    current_validation = {
        scenario_id
        for scenario_id, split in current.items()
        if split == "validation"
    }

    if not current_validation:
        raise ValueError("Current validation split is empty")

    historical_report_ids = {
        model: historical_validation_ids(report)
        for model, report in historical_reports.items()
    }

    historical_validation = {
        scenario_id
        for scenario_id, split in historical.items()
        if split == "validation"
    }

    report_consistency = {
        model: ids == historical_validation
        for model, ids in historical_report_ids.items()
    }

    historical_assignments_for_current_validation = {
        scenario_id: historical.get(scenario_id, "absent")
        for scenario_id in sorted(current_validation)
    }

    historical_training_overlap = sorted(
        scenario_id
        for scenario_id in current_validation
        if historical.get(scenario_id) == "train"
    )

    distribution = dict(
        sorted(
            Counter(
                historical_assignments_for_current_validation.values()
            ).items()
        )
    )

    return {
        "historical_scenario_count": len(historical),
        "current_scenario_count": len(current),
        "current_validation_scenario_count": len(current_validation),
        "historical_validation_scenario_count": len(
            historical_validation
        ),
        "historical_report_validation_matches_manifest": (
            report_consistency
        ),
        "historical_reports_share_validation_ids": (
            len(set(map(frozenset, historical_report_ids.values()))) == 1
        ),
        "historical_assignments_for_current_validation": (
            historical_assignments_for_current_validation
        ),
        "historical_split_distribution_for_current_validation": (
            distribution
        ),
        "historical_training_overlap_count": len(
            historical_training_overlap
        ),
        "historical_training_overlap_ids": historical_training_overlap,
        "historical_manifest_matches_current": historical == current,
        "checkpoint_training_membership_verified": False,
        "independent_validation_status": "unverified",
        "weight_level_leakage_status": "not_established",
    }


def evaluate_integrity() -> dict:
    """Run the read-only provenance audit on existing metadata."""
    historical_manifest = load_historical_manifest()

    current_manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    reports = {
        model: json.loads(
            (REPORT_DIR / filename).read_text(encoding="utf-8")
        )
        for model, filename in HISTORICAL_REPORTS.items()
    }

    comparison = compare_split_provenance(
        historical_manifest,
        current_manifest,
        reports,
    )

    return {
        "task": "RW-140-4",
        "status": "historical_split_provenance_audit",
        "checkpoint_commit": CHECKPOINT_COMMIT,
        "comparison": comparison,
        "limitations": [
            "Historical split assignments are not direct evidence of "
            "checkpoint weight-level training membership.",
            "Current validation contains scenarios historically assigned "
            "to training.",
            "Independent validation of saved checkpoints is unverified.",
            "Historical validation records do not establish training IDs.",
            "No checkpoint weights are loaded or modified.",
            "No frozen final holdout is accessed or evaluated.",
            "No real-world model generalization is established.",
        ],
        "real_action_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_integrity(), indent=2))
