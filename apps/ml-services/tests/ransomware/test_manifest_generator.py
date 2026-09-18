from pathlib import Path

from config.ransomware.scenarios.manifest_generator import (
    build_manifest,
    manifest_to_json,
)


def test_manifest_contains_required_metadata(tmp_path: Path):
    observable = tmp_path / "observable.json"
    observable.write_text('{"event":"synthetic"}')

    manifest = build_manifest(
        generator_version="0.1.0",
        seed=42,
        scenario_family="normal",
        industry="energy",
        site="energy-blr01",
        row_counts={"observable": 1},
        time_range={
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-01T00:01:00Z",
        },
        files=[observable],
        truth_file_references=["truth/scenario/example.json"],
    )

    assert manifest.generator_version == "0.1.0"
    assert manifest.seed == 42
    assert manifest.scenario_family == "normal"
    assert manifest.industry == "energy"
    assert manifest.site == "energy-blr01"
    assert manifest.row_counts
    assert manifest.time_range
    assert manifest.file_hashes
    assert manifest.truth_file_references


def test_manifest_hash_is_deterministic(tmp_path: Path):
    observable = tmp_path / "observable.json"
    observable.write_text('{"event":"synthetic"}')

    first = build_manifest(
        generator_version="0.1.0",
        seed=42,
        scenario_family="normal",
        industry="energy",
        site="energy-blr01",
        row_counts={"observable": 1},
        time_range={},
        files=[observable],
        truth_file_references=[],
    )

    second = build_manifest(
        generator_version="0.1.0",
        seed=42,
        scenario_family="normal",
        industry="energy",
        site="energy-blr01",
        row_counts={"observable": 1},
        time_range={},
        files=[observable],
        truth_file_references=[],
    )

    assert first.file_hashes == second.file_hashes


def test_manifest_json_is_serializable(tmp_path: Path):
    observable = tmp_path / "observable.json"
    observable.write_text("{}")

    manifest = build_manifest(
        generator_version="0.1.0",
        seed=7,
        scenario_family="fault",
        industry="petrochemical",
        site="petrochemical-mng01",
        row_counts={"observable": 1},
        time_range={},
        files=[observable],
        truth_file_references=[],
    )

    output = manifest_to_json(manifest)

    assert '"generator_version": "0.1.0"' in output
    assert '"seed": 7' in output
    assert '"file_hashes"' in output


def test_hash_changes_when_file_changes(tmp_path: Path):
    observable = tmp_path / "observable.json"
    observable.write_text("first")

    first = build_manifest(
        generator_version="0.1.0",
        seed=42,
        scenario_family="normal",
        industry="energy",
        site="energy-blr01",
        row_counts={},
        time_range={},
        files=[observable],
        truth_file_references=[],
    )

    observable.write_text("second")

    second = build_manifest(
        generator_version="0.1.0",
        seed=42,
        scenario_family="normal",
        industry="energy",
        site="energy-blr01",
        row_counts={},
        time_range={},
        files=[observable],
        truth_file_references=[],
    )

    assert first.file_hashes != second.file_hashes
