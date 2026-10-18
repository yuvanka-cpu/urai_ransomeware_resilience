"""Cycle 3 development/calibration asset-grouped split assignments.

No holdout is created here. Historical Cycle 2 datasets and frozen
evaluation artifacts remain unchanged.
"""

import hashlib
from dataclasses import dataclass

from config.ransomware.scenarios.sector_compatible_cycle3 import (
    build_sector_compatible_scenarios,
)


SPLIT_VERSION = "cycle3_asset_grouped_v1"
DEFAULT_SEED = 20261017

DEVELOPMENT_ASSET_COUNTS = {
    "energy": 7,
    "petrochemical": 8,
}

SECTORS = ("energy", "petrochemical")


@dataclass(frozen=True)
class Cycle3SplitAssignment:
    sector: str
    asset_id: str
    split: str
    use_case_id: str
    variant: str


@dataclass(frozen=True)
class Cycle3SplitManifest:
    version: str
    seed: int
    assignments: tuple[Cycle3SplitAssignment, ...]


def _asset_rank(seed: int, sector: str, asset_id: str) -> str:
    material = f"{SPLIT_VERSION}|{seed}|{sector}|{asset_id}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_cycle3_split_manifest(
    seed: int = DEFAULT_SEED,
) -> Cycle3SplitManifest:
    """Assign whole assets to development or calibration."""

    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    assignments = []

    for sector in SECTORS:
        batch = build_sector_compatible_scenarios(sector)

        ranked_assets = sorted(
            batch.asset_ids,
            key=lambda asset: (_asset_rank(seed, sector, asset), asset),
        )

        development_count = DEVELOPMENT_ASSET_COUNTS[sector]

        if not 0 < development_count < len(ranked_assets):
            raise ValueError("Invalid development asset quota")

        development_assets = set(ranked_assets[:development_count])

        for scenario in batch.scenarios:
            split = (
                "development"
                if scenario.asset_id in development_assets
                else "calibration"
            )

            assignments.append(
                Cycle3SplitAssignment(
                    sector=sector,
                    asset_id=scenario.asset_id,
                    split=split,
                    use_case_id=scenario.use_case_id,
                    variant=scenario.variant,
                )
            )

    return Cycle3SplitManifest(
        version=SPLIT_VERSION,
        seed=seed,
        assignments=tuple(assignments),
    )
