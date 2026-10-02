"""RW-100-1 promoted artifact loader and runtime validation.

Synthetic ransomware-resilience PoC only.

Loads only the declared RW-090-6 promoted bundle. Every manifest-listed
artifact is validated for existence, size, SHA-256, and runtime compatibility.
No alternate artifact is selected when validation fails.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.ransomware.rw0905_artifact_availability import (
    ArtifactHealth,
    ArtifactStatus,
    FailureReason,
    validate_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIR = ROOT / "artifacts/ransomware/promoted/rw0906_v1"
MANIFEST_PATH = BUNDLE_DIR / "bundle_manifest.json"

EXPECTED_BUNDLE_VERSION = "rw0906_v1"
EXPECTED_CHECKSUM_ALGORITHM = "SHA-256"
EXPECTED_FILE_COUNT = 12

REQUIRED_RUNTIME_VERSIONS = {
    "python": "3.12.10",
    "catboost": "1.2.10",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "scikit-learn": "1.9.1",
    "torch": "2.8.0+cpu",
}


@dataclass(frozen=True)
class LoadedArtifact:
    artifact_role: str
    relative_path: str
    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class LoadedBundle:
    bundle_version: str
    artifacts: tuple[LoadedArtifact, ...]
    manifest: dict[str, Any]


class ArtifactLoadError(RuntimeError):
    """Raised when the promoted bundle cannot be used safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _read_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise ArtifactLoadError(
            f"unavailable: promoted bundle manifest is missing: {MANIFEST_PATH}"
        )

    if not MANIFEST_PATH.is_file():
        raise ArtifactLoadError(
            f"unavailable: promoted bundle manifest is not a file: {MANIFEST_PATH}"
        )

    try:
        payload = json.loads(
            MANIFEST_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactLoadError(
            f"unavailable: promoted bundle manifest is corrupt: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ArtifactLoadError(
            "unavailable: promoted bundle manifest must be a JSON object"
        )

    return payload


def _validate_manifest_contract(
    manifest: dict[str, Any],
) -> None:
    if manifest.get("artifact_type") != "versioned_promoted_artifact_bundle":
        raise ArtifactLoadError(
            "unavailable: incompatible promoted bundle artifact_type"
        )

    if manifest.get("bundle_version") != EXPECTED_BUNDLE_VERSION:
        raise ArtifactLoadError(
            "unavailable: incompatible promoted bundle version: "
            f"{manifest.get('bundle_version')!r}"
        )

    checksums = manifest.get("checksums")

    if not isinstance(checksums, dict):
        raise ArtifactLoadError(
            "unavailable: incompatible checksum contract"
        )

    if checksums.get("algorithm") != EXPECTED_CHECKSUM_ALGORITHM:
        raise ArtifactLoadError(
            "unavailable: incompatible checksum algorithm"
        )

    if checksums.get("all_files_checksummed") is not True:
        raise ArtifactLoadError(
            "unavailable: bundle does not declare all files checksummed"
        )

    if checksums.get("file_count") != EXPECTED_FILE_COUNT:
        raise ArtifactLoadError(
            "unavailable: incompatible bundle file count: "
            f"{checksums.get('file_count')!r}"
        )

    files = manifest.get("files")

    if not isinstance(files, list):
        raise ArtifactLoadError(
            "unavailable: manifest files must be a list"
        )

    if len(files) != EXPECTED_FILE_COUNT:
        raise ArtifactLoadError(
            "unavailable: manifest file count mismatch: "
            f"expected={EXPECTED_FILE_COUNT}, actual={len(files)}"
        )


def _validate_runtime_versions(
    manifest: dict[str, Any],
) -> None:
    environment = manifest.get("environment")

    if not isinstance(environment, dict):
        raise ArtifactLoadError(
            "unavailable: runtime environment contract is missing"
        )

    versions = environment.get("versions")

    if not isinstance(versions, dict):
        raise ArtifactLoadError(
            "unavailable: runtime version contract is missing"
        )

    actual_runtime = {
        "python": platform.python_version(),
        "catboost": _package_version("catboost"),
        "numpy": _package_version("numpy"),
        "pandas": _package_version("pandas"),
        "scikit-learn": _package_version("sklearn"),
        "torch": _package_version("torch"),
    }

    for package, expected in REQUIRED_RUNTIME_VERSIONS.items():
        declared = versions.get(package)

        if declared != expected:
            raise ArtifactLoadError(
                "unavailable: manifest runtime version mismatch for "
                f"{package}: declared={declared!r}, expected={expected!r}"
            )

        if actual_runtime[package] != expected:
            raise ArtifactLoadError(
                "unavailable: installed runtime version mismatch for "
                f"{package}: expected={expected!r}, "
                f"actual={actual_runtime[package]!r}"
            )


def _package_version(module_name: str) -> str:
    module = __import__(module_name)
    return str(module.__version__)


def _validate_artifacts(
    manifest: dict[str, Any],
) -> tuple[LoadedArtifact, ...]:
    loaded: list[LoadedArtifact] = []

    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ArtifactLoadError(
                "unavailable: malformed manifest artifact entry"
            )

        relative_path = entry.get("path")
        expected_sha256 = entry.get("sha256")
        expected_size = entry.get("size_bytes")
        artifact_role = entry.get("artifact_role")

        if not all(
            isinstance(value, str) and value
            for value in (
                relative_path,
                expected_sha256,
                artifact_role,
            )
        ):
            raise ArtifactLoadError(
                "unavailable: malformed artifact manifest entry"
            )

        if not isinstance(expected_size, int) or expected_size < 0:
            raise ArtifactLoadError(
                f"unavailable: invalid declared size for {relative_path}"
            )

        path = BUNDLE_DIR / relative_path

        try:
            path.relative_to(BUNDLE_DIR)
        except ValueError as exc:
            raise ArtifactLoadError(
                f"unavailable: artifact path escapes promoted bundle: "
                f"{relative_path}"
            ) from exc

        health: ArtifactHealth = validate_artifact(
            artifact_id=relative_path,
            path=path,
            expected_sha256=expected_sha256,
        )

        if health.status is not ArtifactStatus.AVAILABLE:
            raise ArtifactLoadError(
                f"unavailable: {relative_path}: "
                f"{health.failure_reason.value}: {health.detail}"
            )

        actual_size = path.stat().st_size

        if actual_size != expected_size:
            raise ArtifactLoadError(
                f"unavailable: {relative_path}: size mismatch: "
                f"expected={expected_size}, actual={actual_size}"
            )

        loaded.append(
            LoadedArtifact(
                artifact_role=artifact_role,
                relative_path=relative_path,
                path=path,
                sha256=expected_sha256,
                size_bytes=actual_size,
            )
        )

    return tuple(loaded)


def load_promoted_bundle() -> LoadedBundle:
    """Validate and load the exact promoted RW-090-6 bundle."""

    manifest = _read_manifest()
    _validate_manifest_contract(manifest)
    _validate_runtime_versions(manifest)

    artifacts = _validate_artifacts(manifest)

    return LoadedBundle(
        bundle_version=manifest["bundle_version"],
        artifacts=artifacts,
        manifest=manifest,
    )


def main() -> None:
    bundle = load_promoted_bundle()

    print("=== RW-100-1 COMPLETE ===")
    print("Bundle:", bundle.bundle_version)
    print("Validated artifacts:", len(bundle.artifacts))
    print("Checksum algorithm:", EXPECTED_CHECKSUM_ALGORITHM)
    print("Runtime versions: compatible")
    print("Silent substitution: forbidden")
    print("Status: available")


if __name__ == "__main__":
    main()
