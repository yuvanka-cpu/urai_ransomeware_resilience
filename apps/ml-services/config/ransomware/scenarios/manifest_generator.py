from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class ScenarioManifest:
    generator_version: str
    seed: int
    scenario_family: str
    industry: str
    site: str
    row_counts: dict[str, int]
    time_range: dict[str, str]
    file_hashes: dict[str, str]
    truth_file_references: list[str]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(
    *,
    generator_version: str,
    seed: int,
    scenario_family: str,
    industry: str,
    site: str,
    row_counts: dict[str, int],
    time_range: dict[str, str],
    files: list[Path],
    truth_file_references: list[str],
) -> ScenarioManifest:
    hashes = {
        str(path): sha256_file(path)
        for path in files
    }

    return ScenarioManifest(
        generator_version=generator_version,
        seed=seed,
        scenario_family=scenario_family,
        industry=industry,
        site=site,
        row_counts=row_counts,
        time_range=time_range,
        file_hashes=hashes,
        truth_file_references=truth_file_references,
    )


def manifest_to_json(manifest: ScenarioManifest) -> str:
    return json.dumps(
        manifest.__dict__,
        indent=2,
        sort_keys=True,
    )
