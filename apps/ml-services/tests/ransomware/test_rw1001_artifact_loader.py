from pathlib import Path

import pytest

from config.ransomware import rw1001_artifact_loader as loader


def test_promoted_bundle_loads():
    bundle = loader.load_promoted_bundle()

    assert bundle.bundle_version == "rw0906_v1"
    assert len(bundle.artifacts) == 12


def test_missing_manifest_fails(monkeypatch, tmp_path):
    missing_manifest = tmp_path / "missing_bundle_manifest.json"

    monkeypatch.setattr(loader, "MANIFEST_PATH", missing_manifest)

    with pytest.raises(loader.ArtifactLoadError, match="manifest is missing"):
        loader.load_promoted_bundle()


def test_checksum_tampering_fails(monkeypatch, tmp_path):
    original_bundle_dir = loader.BUNDLE_DIR
    test_bundle = tmp_path / "rw0906_v1"
    test_bundle.mkdir()

    manifest = loader._read_manifest()
    first_entry = manifest["files"][0]

    source = original_bundle_dir / first_entry["path"]
    destination = test_bundle / first_entry["path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes() + b"\nTAMPERED")

    first_entry["sha256"] = loader.sha256_file(source)

    manifest_path = test_bundle / "bundle_manifest.json"
    manifest_path.write_text(
        __import__("json").dumps(manifest),
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "BUNDLE_DIR", test_bundle)
    monkeypatch.setattr(loader, "MANIFEST_PATH", manifest_path)

    with pytest.raises(loader.ArtifactLoadError, match="checksum"):
        loader.load_promoted_bundle()


def test_incompatible_bundle_version_fails(monkeypatch, tmp_path):
    manifest = loader._read_manifest()
    manifest["bundle_version"] = "rw9999_incompatible"

    manifest_path = tmp_path / "bundle_manifest.json"
    manifest_path.write_text(
        __import__("json").dumps(manifest),
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "MANIFEST_PATH", manifest_path)

    with pytest.raises(
        loader.ArtifactLoadError,
        match="incompatible promoted bundle version",
    ):
        loader.load_promoted_bundle()
