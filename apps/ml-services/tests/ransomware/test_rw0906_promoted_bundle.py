import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "ransomware" / "promoted" / "rw0906_v1"
MANIFEST = BUNDLE / "bundle_manifest.json"


def test_rw0906_bundle_integrity():
    assert MANIFEST.is_file()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["task"] == "RW-090-6"
    assert manifest["bundle_version"] == "rw0906_v1"
    assert manifest["synthetic_only"] is True

    assert manifest["promotion_boundary"]["rejected_challengers_excluded"] is True

    assert manifest["promotion_boundary"]["runtime_chain"] == [
        "rw0704_catboost",
        "rw0902_logistic_stacking",
        "rw0903_sector_calibration",
        "rw0904_threshold_policy",
    ]

    paths = {entry["path"] for entry in manifest["files"]}

    assert "contracts/feature_contract.md" in paths

    rejected_names = {
        "rw0801_tabpfn_challenger_report.json",
        "rw0802_tcn_model.pt",
        "rw0803_transformer_model.pt",
        "rw0805_graph_challenger_report.json",
    }

    assert not any(
        Path(path).name in rejected_names
        for path in paths
    )

    assert manifest["checksums"]["algorithm"] == "SHA-256"
    assert manifest["checksums"]["all_files_checksummed"] is True

    for entry in manifest["files"]:
        path = BUNDLE / entry["path"]

        assert path.is_file(), f"Missing bundled file: {entry['path']}"

        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

        assert actual_sha256 == entry["sha256"], (
            f"Checksum mismatch: {entry['path']}"
        )

        assert entry["size_bytes"] == path.stat().st_size


def test_rw0906_required_library_versions_present():
    versions = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )["environment"]["versions"]

    for package in [
        "python",
        "catboost",
        "numpy",
        "pandas",
        "scikit-learn",
        "torch",
    ]:
        assert versions.get(package)
        assert versions[package] != "unavailable"


def test_rw0906_runtime_safety_contract():
    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    contract = manifest["runtime_contract"]

    assert contract["human_approval_required"] is True
    assert contract["real_action_executed"] is False
    assert contract["physical_safety_determination"] == "not_determined"
    assert contract["operational_state_claimed"] is False
