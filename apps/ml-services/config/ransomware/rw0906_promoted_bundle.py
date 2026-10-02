"""RW-090-6 versioned promoted-artifact bundle.

Synthetic ransomware-resilience PoC only.

Packages only the currently promoted runtime chain:
    CatBoost -> Logistic Stacking -> Sector Calibration -> Threshold Policy

Rejected challengers are intentionally excluded.
Every bundled file receives a SHA-256 checksum.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "ransomware"
MODEL_DIR = ARTIFACT_ROOT / "models"
OFFLINE_DIR = ARTIFACT_ROOT / "offline"
BUNDLE_ROOT = ARTIFACT_ROOT / "promoted"
BUNDLE_DIR = BUNDLE_ROOT / "rw0906_v1"

MANIFEST_PATH = BUNDLE_DIR / "bundle_manifest.json"


PROMOTED_FILES = [
    (
        "models/rw0704_catboost_model.cbm",
        MODEL_DIR / "rw0704_catboost_model.cbm",
        "promoted_model",
    ),
    (
        "models/rw0704_catboost_training_manifest.json",
        MODEL_DIR / "rw0704_catboost_training_manifest.json",
        "training_lineage",
    ),
    (
        "models/rw0902_logistic_stacking_model.json",
        MODEL_DIR / "rw0902_logistic_stacking_model.json",
        "promoted_model",
    ),
    (
        "models/rw0903_sector_calibrators.json",
        MODEL_DIR / "rw0903_sector_calibrators.json",
        "calibrator",
    ),
    (
        "offline/rw0902_logistic_stacking_report.json",
        OFFLINE_DIR / "rw0902_logistic_stacking_report.json",
        "metric_report",
    ),
    (
        "offline/rw0903_sector_calibration_report.json",
        OFFLINE_DIR / "rw0903_sector_calibration_report.json",
        "calibration_report",
    ),
    (
        "offline/rw0904_threshold_policy_report.json",
        OFFLINE_DIR / "rw0904_threshold_policy_report.json",
        "threshold_policy",
    ),
    (
        "offline/rw0905_artifact_failure_matrix.json",
        OFFLINE_DIR / "rw0905_artifact_failure_matrix.json",
        "availability_contract",
    ),
    (
        "offline/rw0807_promotion_decision.json",
        OFFLINE_DIR / "rw0807_promotion_decision.json",
        "promotion_decision",
    ),
    (
        "offline/rw0609_feature_parity_report.json",
        OFFLINE_DIR / "rw0609_feature_parity_report.json",
        "feature_contract_evidence",
    ),
    (
        "contracts/feature_contract.md",
        ROOT / "config" / "ransomware" / "shared" / "schemas" / "feature_contract.md",
        "feature_contract",
    ),
    (
        "offline/split_assignment_manifest.json",
        OFFLINE_DIR / "split_assignment_manifest.json",
        "split_lineage",
    ),
]

REJECTED_FILES = [
    "offline/rw0801_tabpfn_challenger_report.json",
    "offline/rw0802_tcn_model.pt",
    "offline/rw0802_tcn_report.json",
    "offline/rw0803_transformer_model.pt",
    "offline/rw0803_transformer_report.json",
    "offline/rw0805_graph_challenger_report.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_files() -> None:
    missing = [
        str(source.relative_to(ROOT))
        for _, source, _ in PROMOTED_FILES
        if not source.is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required promoted artifacts:\n" + "\n".join(missing)
        )


def validate_promotion_boundary() -> dict[str, Any]:
    decision_path = OFFLINE_DIR / "rw0807_promotion_decision.json"
    decision = load_json(decision_path)

    if decision.get("decision") != "NO_CHALLENGER_PROMOTED":
        raise ValueError(
            "RW-080-7 does not state NO_CHALLENGER_PROMOTED; "
            "promotion boundary cannot be established safely."
        )

    rejected_paths = [
        str(OFFLINE_DIR / Path(name).name)
        for name in REJECTED_FILES
    ]

    return {
        "rw0807_decision": decision.get("decision"),
        "rejected_challenger_artifacts_excluded": True,
        "excluded_candidates": REJECTED_FILES,
    }


def copy_promoted_files() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for bundle_relative, source, artifact_role in PROMOTED_FILES:
        destination = BUNDLE_DIR / bundle_relative
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)

        entries.append(
            {
                "path": bundle_relative.replace("\\", "/"),
                "source_path": str(source.relative_to(ROOT)).replace("\\", "/"),
                "artifact_role": artifact_role,
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        )

    return entries


def build_environment_record() -> dict[str, Any]:
    versions: dict[str, str] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }

    for package, module_name in [
        ("catboost", "catboost"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scikit-learn", "sklearn"),
        ("torch", "torch"),
    ]:
        try:
            module = __import__(module_name)
            versions[package] = getattr(module, "__version__", "unknown")
        except Exception:
            versions[package] = "unavailable"

    return {
        "python_executable": sys.executable,
        "versions": versions,
    }


def build_manifest(entries: list[dict[str, Any]]) -> dict[str, Any]:
    catboost_manifest = load_json(
        MODEL_DIR / "rw0704_catboost_training_manifest.json"
    )
    stacking_model = load_json(
        MODEL_DIR / "rw0902_logistic_stacking_model.json"
    )
    calibrator = load_json(
        MODEL_DIR / "rw0903_sector_calibrators.json"
    )
    threshold_report = load_json(
        OFFLINE_DIR / "rw0904_threshold_policy_report.json"
    )
    availability = load_json(
        OFFLINE_DIR / "rw0905_artifact_failure_matrix.json"
    )

    return {
        "task": "RW-090-6",
        "artifact_type": "versioned_promoted_artifact_bundle",
        "bundle_version": "rw0906_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "synthetic_only": True,

        "promotion_boundary": {
            "runtime_chain": [
                "rw0704_catboost",
                "rw0902_logistic_stacking",
                "rw0903_sector_calibration",
                "rw0904_threshold_policy",
            ],
            "challenger_promotion_status": "NO_CHALLENGER_PROMOTED",
            "rejected_challengers_excluded": True,
        },

        "files": entries,

        "training_lineage": {
            "catboost_manifest_version": catboost_manifest.get(
                "manifest_version"
            ),
            "catboost_version": catboost_manifest.get(
                "catboost_version"
            ),
            "base_seed": catboost_manifest.get("base_seed"),
            "scenario_count": catboost_manifest.get("scenario_count"),
            "observable_feature_count": catboost_manifest.get(
                "observable_feature_count"
            ),
            "model_input_feature_count": catboost_manifest.get(
                "model_input_feature_count"
            ),
            "windows_minutes": catboost_manifest.get("windows_minutes"),
            "splits_used_for_training": catboost_manifest.get(
                "splits_used_for_training"
            ),
            "scenario_group_leakage_excluded": catboost_manifest.get(
                "scenario_group_leakage_excluded"
            ),
            "label_leakage_excluded": catboost_manifest.get(
                "label_leakage_excluded"
            ),
            "source_split_manifest": catboost_manifest.get(
                "source_split_manifest"
            ),
            "source_split_manifest_sha256": catboost_manifest.get(
                "source_split_manifest_sha256"
            ),
        },

        "stacking": {
            "model_type": stacking_model.get("model_type"),
            "algorithm": stacking_model.get("algorithm"),
            "components": stacking_model.get("components"),
            "feature_names": stacking_model.get("feature_names"),
            "missing_indicator_columns": stacking_model.get(
                "missing_indicator_columns"
            ),
            "direct_score_averaging": False,
        },

        "calibration": {
            "method": calibrator.get("method"),
            "sector_calibrators": list(
                calibrator.get("sector_calibrators", {}).keys()
            ),
            "global_fallback_present": "global_calibrator" in calibrator,
            "training_scope": calibrator.get("training_scope"),
        },

        "threshold_policy": {
            "candidate_policy": threshold_report[
                "threshold_policy"
            ]["candidate_policy"],
            "investigate_threshold": threshold_report[
                "selection"
            ]["selected"]["investigate_threshold"],
            "high_risk_threshold": threshold_report[
                "selection"
            ]["selected"]["high_risk_threshold"],
            "selection_cost": threshold_report[
                "selection"
            ]["selected"]["total_cost"],
            "thresholds_frozen_before_final_holdout": threshold_report[
                "training_scope"
            ]["thresholds_frozen_before_final_holdout"],
        },

        "availability_contract": {
            "silent_substitution_forbidden": availability[
                "contract"
            ]["silent_substitution_forbidden"],
            "missing_is_unavailable": availability[
                "contract"
            ]["missing_is_unavailable"],
            "corrupt_is_unavailable": availability[
                "contract"
            ]["corrupt_is_unavailable"],
            "stale_is_unavailable": availability[
                "contract"
            ]["stale_is_unavailable"],
            "incompatible_is_unavailable": availability[
                "contract"
            ]["incompatible_is_unavailable"],
            "slow_is_unavailable": availability[
                "contract"
            ]["slow_is_unavailable"],
        },

        "runtime_contract": {
            "human_approval_required": True,
            "real_action_executed": False,
            "physical_safety_determination": "not_determined",
            "operational_state_claimed": False,
        },

        "environment": build_environment_record(),

        "checksums": {
            "algorithm": "SHA-256",
            "file_count": len(entries),
            "all_files_checksummed": True,
        },
    }


def main() -> None:
    validate_source_files()
    validate_promotion_boundary()

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    entries = copy_promoted_files()
    manifest = build_manifest(entries)

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_sha256 = sha256_file(MANIFEST_PATH)

    print("=== RW-090-6 COMPLETE ===")
    print(f"Bundle: {BUNDLE_DIR}")
    print(f"Files: {len(entries)}")
    print(f"Manifest SHA-256: {manifest_sha256}")
    print("Rejected challengers excluded: True")


if __name__ == "__main__":
    main()
