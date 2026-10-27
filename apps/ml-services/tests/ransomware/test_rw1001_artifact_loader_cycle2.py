import copy
import json
from pathlib import Path

import pytest

from config.ransomware import rw1001_artifact_loader_cycle2 as loader


def _valid_manifest():
    return json.loads(loader.MANIFEST_PATH.read_text(encoding="utf-8"))


def test_cycle2_manifest_accepts_promoted_bundle_contract():
    manifest = _valid_manifest()

    assert loader._validate_manifest_contract(manifest) is None
    assert manifest["bundle_version"] == "rw0906_v2"
    assert manifest["checksums"]["algorithm"] == "SHA-256"
    assert manifest["checksums"]["file_count"] == 12
    assert len(manifest["files"]) == 12


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda manifest: manifest.update(
                artifact_type="unexpected_bundle"
            ),
            "artifact_type",
        ),
        (
            lambda manifest: manifest.update(bundle_version="rw0906_v1"),
            "bundle version",
        ),
        (
            lambda manifest: manifest.update(checksums=None),
            "checksum contract",
        ),
        (
            lambda manifest: manifest["checksums"].update(
                algorithm="MD5"
            ),
            "checksum algorithm",
        ),
        (
            lambda manifest: manifest["checksums"].update(
                all_files_checksummed=False
            ),
            "all files checksummed",
        ),
        (
            lambda manifest: manifest["checksums"].update(file_count=11),
            "file count",
        ),
        (
            lambda manifest: manifest.update(files="not-a-list"),
            "files must be a list",
        ),
        (
            lambda manifest: manifest["files"].pop(),
            "manifest file count mismatch",
        ),
    ],
)
def test_cycle2_manifest_rejects_incompatible_contract(mutate, message):
    manifest = copy.deepcopy(_valid_manifest())
    mutate(manifest)

    with pytest.raises(loader.ArtifactLoadError, match=message):
        loader._validate_manifest_contract(manifest)


def test_cycle2_missing_manifest_is_unavailable(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(loader, "MANIFEST_PATH", tmp_path / "missing.json")

    with pytest.raises(loader.ArtifactLoadError, match="manifest is missing"):
        loader._read_manifest()


def test_cycle2_corrupt_manifest_is_unavailable(tmp_path: Path, monkeypatch):
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text("{invalid json", encoding="utf-8")
    monkeypatch.setattr(loader, "MANIFEST_PATH", manifest_path)

    with pytest.raises(loader.ArtifactLoadError, match="manifest is corrupt"):
        loader._read_manifest()


def test_cycle2_non_object_manifest_is_unavailable(tmp_path: Path, monkeypatch):
    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(loader, "MANIFEST_PATH", manifest_path)

    with pytest.raises(loader.ArtifactLoadError, match="JSON object"):
        loader._read_manifest()


def _temporary_bundle(tmp_path: Path, monkeypatch, content: bytes = b"safe-test-artifact"):
    import hashlib

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    artifact = bundle_dir / "artifact.bin"
    artifact.write_bytes(content)

    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(loader, "BUNDLE_DIR", bundle_dir)
    return {
        "files": [
            {
                "artifact_role": "test_artifact",
                "path": "artifact.bin",
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        ]
    }, artifact


def test_cycle2_artifact_validation_accepts_matching_hash_and_size(
    tmp_path: Path, monkeypatch
):
    manifest, artifact = _temporary_bundle(tmp_path, monkeypatch)

    loaded = loader._validate_artifacts(manifest)

    assert len(loaded) == 1
    assert loaded[0].path == artifact.resolve()
    assert loaded[0].size_bytes == artifact.stat().st_size
    assert loaded[0].artifact_role == "test_artifact"


def test_cycle2_artifact_validation_rejects_checksum_mismatch(
    tmp_path: Path, monkeypatch
):
    manifest, _ = _temporary_bundle(tmp_path, monkeypatch)
    manifest["files"][0]["sha256"] = "0" * 64

    with pytest.raises(loader.ArtifactLoadError, match="corrupt"):
        loader._validate_artifacts(manifest)


def test_cycle2_artifact_validation_rejects_size_mismatch(
    tmp_path: Path, monkeypatch
):
    manifest, _ = _temporary_bundle(tmp_path, monkeypatch)
    manifest["files"][0]["size_bytes"] += 1

    with pytest.raises(loader.ArtifactLoadError, match="size mismatch"):
        loader._validate_artifacts(manifest)


@pytest.mark.parametrize("unsafe_path", ["../outside.bin", "/outside.bin"])
def test_cycle2_artifact_validation_rejects_unsafe_paths(
    tmp_path: Path, monkeypatch, unsafe_path: str
):
    manifest, _ = _temporary_bundle(tmp_path, monkeypatch)
    manifest["files"][0]["path"] = unsafe_path

    with pytest.raises(loader.ArtifactLoadError, match="escapes promoted bundle"):
        loader._validate_artifacts(manifest)


def test_cycle2_artifact_validation_rejects_missing_file(
    tmp_path: Path, monkeypatch
):
    manifest, _ = _temporary_bundle(tmp_path, monkeypatch)
    manifest["files"][0]["path"] = "missing.bin"

    with pytest.raises(loader.ArtifactLoadError, match="missing"):
        loader._validate_artifacts(manifest)


def test_cycle2_artifact_validation_rejects_malformed_entry(
    tmp_path: Path, monkeypatch
):
    manifest, _ = _temporary_bundle(tmp_path, monkeypatch)
    manifest["files"][0] = "not-an-artifact-object"

    with pytest.raises(loader.ArtifactLoadError, match="malformed manifest artifact entry"):
        loader._validate_artifacts(manifest)


def _runtime_manifest():
    manifest = _valid_manifest()
    manifest["environment"]["versions"] = dict(
        loader.REQUIRED_RUNTIME_VERSIONS
    )
    return manifest


def test_cycle2_runtime_accepts_matching_versions(monkeypatch):
    manifest = _runtime_manifest()

    monkeypatch.setattr(loader.platform, "python_version", lambda: "3.12.10")
    monkeypatch.setattr(
        loader,
        "_package_version",
        lambda module_name: {
            "catboost": "1.2.10",
            "numpy": "2.5.3",
            "pandas": "3.0.6",
            "sklearn": "1.9.1",
            "torch": "2.8.0+cpu",
        }[module_name],
    )

    assert loader._validate_runtime_versions(manifest) is None


def test_cycle2_runtime_rejects_missing_environment():
    with pytest.raises(loader.ArtifactLoadError, match="runtime environment contract"):
        loader._validate_runtime_versions({})


def test_cycle2_runtime_rejects_missing_versions():
    with pytest.raises(
        loader.ArtifactLoadError, match="runtime version contract"
    ):
        loader._validate_runtime_versions({"environment": {}})


def test_cycle2_runtime_rejects_manifest_version_mismatch():
    manifest = _runtime_manifest()
    manifest["environment"]["versions"]["numpy"] = "0.0.0"

    with pytest.raises(
        loader.ArtifactLoadError,
        match="manifest runtime version mismatch for numpy",
    ):
        loader._validate_runtime_versions(manifest)


def test_cycle2_runtime_rejects_installed_version_mismatch(monkeypatch):
    manifest = _runtime_manifest()

    monkeypatch.setattr(loader.platform, "python_version", lambda: "3.12.10")
    monkeypatch.setattr(
        loader,
        "_package_version",
        lambda module_name: {
            "catboost": "1.2.10",
            "numpy": "0.0.0",
            "pandas": "3.0.6",
            "sklearn": "1.9.1",
            "torch": "2.8.0+cpu",
        }[module_name],
    )

    with pytest.raises(
        loader.ArtifactLoadError,
        match="installed runtime version mismatch for numpy",
    ):
        loader._validate_runtime_versions(manifest)
