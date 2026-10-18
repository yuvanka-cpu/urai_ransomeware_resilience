"""Cycle 3 synthetic development asset compatibility validation.

This module classifies asset identifiers against canonical sector graphs.

It does not modify scenarios, execute graph propagation, perform model
inference, or determine cyber/physical risk.
"""

from dataclasses import dataclass
from typing import Literal

from config.ransomware.graph_propagation import load_sector_graph


AssetCompatibilityStatus = Literal[
    "sector_graph_match",
    "cross_sector_asset",
    "absent_from_both_graphs",
]

SUPPORTED_SECTORS = ("energy", "petrochemical")


@dataclass(frozen=True)
class AssetCompatibilityResult:
    sector: str
    asset_id: str
    status: AssetCompatibilityStatus
    compatible: bool
    matched_sector: str | None


def validate_sector_asset(
    sector: str,
    asset_id: str,
) -> AssetCompatibilityResult:
    """Classify an asset without changing its identifier."""

    if sector not in SUPPORTED_SECTORS:
        raise ValueError(
            "sector must be 'energy' or 'petrochemical'"
        )

    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("asset_id must be a non-empty string")

    selected_graph = load_sector_graph(sector)

    if asset_id in selected_graph.assets:
        return AssetCompatibilityResult(
            sector=sector,
            asset_id=asset_id,
            status="sector_graph_match",
            compatible=True,
            matched_sector=sector,
        )

    other_sector = next(
        candidate
        for candidate in SUPPORTED_SECTORS
        if candidate != sector
    )

    other_graph = load_sector_graph(other_sector)

    if asset_id in other_graph.assets:
        return AssetCompatibilityResult(
            sector=sector,
            asset_id=asset_id,
            status="cross_sector_asset",
            compatible=False,
            matched_sector=other_sector,
        )

    return AssetCompatibilityResult(
        sector=sector,
        asset_id=asset_id,
        status="absent_from_both_graphs",
        compatible=False,
        matched_sector=None,
    )
