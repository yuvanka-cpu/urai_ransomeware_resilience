from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config.ransomware.shared.graph_contract import is_valid_edge_type


ROOT = Path(__file__).resolve().parents[2]
GRAPH_ROOT = ROOT / "config" / "ransomware"

# Fixed, auditable weights. These are model-policy constants, not learned values.
EDGE_WEIGHTS = {
    "network_reachability": 0.85,
    "identity_trust": 0.90,
    "service_dependency": 0.85,
    "data_flow": 0.70,
    "backup_coverage": 0.55,
    "recovery_prerequisite": 0.60,
}

CRITICALITY_WEIGHTS = {
    "critical": 1.00,
    "high": 0.80,
    "medium": 0.60,
    "low": 0.40,
}

MAX_HOPS = 8
MIN_PROPAGATION_SCORE = 0.05


@dataclass(frozen=True)
class Asset:
    asset_id: str
    site_id: str
    display_name: str
    asset_type: str
    zone: str
    criticality: str
    recovery_tier: int


@dataclass(frozen=True)
class GraphEdge:
    dependency_id: str
    source_id: str
    target_id: str
    edge_type: str
    weight: float


@dataclass(frozen=True)
class PropagationResult:
    asset_id: str
    score: float
    hops: int
    path: tuple[str, ...]
    edge_types: tuple[str, ...]
    criticality: str
    zone: str
    recovery_tier: int


class WeightedAssetGraph:
    def __init__(
        self,
        assets: dict[str, Asset],
        edges: tuple[GraphEdge, ...],
    ) -> None:
        self.assets = assets
        self.edges = edges
        self._outgoing: dict[str, tuple[GraphEdge, ...]] = {}

        grouped: dict[str, list[GraphEdge]] = {}
        for edge in edges:
            grouped.setdefault(edge.source_id, []).append(edge)

        for source_id, source_edges in grouped.items():
            self._outgoing[source_id] = tuple(
                sorted(
                    source_edges,
                    key=lambda e: (e.target_id, e.dependency_id),
                )
            )

    def propagate(
        self,
        seed_assets: Iterable[str],
        *,
        seed_score: float = 1.0,
        max_hops: int = MAX_HOPS,
        min_score: float = MIN_PROPAGATION_SCORE,
    ) -> list[PropagationResult]:
        """Propagate observed seed evidence through the governed asset graph.

        This is intentionally deterministic. It does not use scenario truth,
        incident-stage truth, affected-asset truth, or future events.
        """
        seeds = tuple(sorted(set(seed_assets)))

        if not seeds:
            return []

        if not 0.0 < seed_score <= 1.0:
            raise ValueError("seed_score must be in (0, 1].")

        if max_hops < 0:
            raise ValueError("max_hops must be >= 0.")

        unknown = [asset_id for asset_id in seeds if asset_id not in self.assets]
        if unknown:
            raise ValueError(f"Unknown seed assets: {unknown}")

        best: dict[str, PropagationResult] = {}

        # Queue entries: asset_id, current_score, hops, path, edge_types.
        queue: list[
            tuple[str, float, int, tuple[str, ...], tuple[str, ...]]
        ] = []

        for asset_id in seeds:
            queue.append(
                (
                    asset_id,
                    seed_score,
                    0,
                    (asset_id,),
                    (),
                )
            )

        while queue:
            asset_id, score, hops, path, edge_types = queue.pop(0)

            asset = self.assets[asset_id]

            # Criticality is reported separately from propagation score so
            # graph topology cannot silently become a severity decision.
            result = PropagationResult(
                asset_id=asset_id,
                score=round(score, 6),
                hops=hops,
                path=path,
                edge_types=edge_types,
                criticality=asset.criticality,
                zone=asset.zone,
                recovery_tier=asset.recovery_tier,
            )

            previous = best.get(asset_id)
            if previous is not None:
                if (
                    previous.score > result.score
                    or (
                        previous.score == result.score
                        and previous.hops <= result.hops
                    )
                ):
                    continue

            best[asset_id] = result

            if hops >= max_hops:
                continue

            for edge in self._outgoing.get(asset_id, ()):
                if edge.target_id in path:
                    continue

                target = self.assets[edge.target_id]

                # Topology weight is combined with a small hop-independent
                # target criticality factor for prioritization only.
                target_factor = CRITICALITY_WEIGHTS[target.criticality]
                next_score = score * edge.weight * target_factor

                if next_score < min_score:
                    continue

                queue.append(
                    (
                        edge.target_id,
                        next_score,
                        hops + 1,
                        path + (edge.target_id,),
                        edge_types + (edge.edge_type,),
                    )
                )

            # Deterministic traversal regardless of dictionary insertion order.
            queue.sort(key=lambda item: (item[2], item[0], item[3]))

        return sorted(
            best.values(),
            key=lambda result: (-result.score, result.hops, result.asset_id),
        )


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_sector_graph(sector: str) -> WeightedAssetGraph:
    if sector not in {"energy", "petrochemical"}:
        raise ValueError("sector must be 'energy' or 'petrochemical'")

    sector_root = GRAPH_ROOT / sector

    assets_payload = _load_json(sector_root / "assets.json")
    edges_payload = _load_json(sector_root / "graph_edges.json")

    if assets_payload.get("sector") != sector:
        raise ValueError("Asset manifest sector does not match requested sector.")

    if edges_payload.get("sector") != sector:
        raise ValueError("Edge manifest sector does not match requested sector.")

    assets: dict[str, Asset] = {}

    for raw in assets_payload.get("assets", []):
        asset = Asset(
            asset_id=raw["asset_id"],
            site_id=raw["site_id"],
            display_name=raw["display_name"],
            asset_type=raw["asset_type"],
            zone=raw["zone"],
            criticality=raw["criticality"],
            recovery_tier=int(raw["recovery_tier"]),
        )

        if asset.asset_id in assets:
            raise ValueError(f"Duplicate asset_id: {asset.asset_id}")

        if asset.criticality not in CRITICALITY_WEIGHTS:
            raise ValueError(
                f"Unsupported criticality: {asset.criticality}"
            )

        assets[asset.asset_id] = asset

    edges: list[GraphEdge] = []

    for raw in edges_payload.get("edges", []):
        edge_type = raw["edge_type"]

        if not is_valid_edge_type(edge_type):
            raise ValueError(f"Unsupported edge type: {edge_type}")

        if edge_type not in EDGE_WEIGHTS:
            raise ValueError(f"Missing weight for edge type: {edge_type}")

        source_id = raw["source_id"]
        target_id = raw["target_id"]

        if source_id not in assets:
            raise ValueError(f"Unknown edge source: {source_id}")

        if target_id not in assets:
            raise ValueError(f"Unknown edge target: {target_id}")

        edges.append(
            GraphEdge(
                dependency_id=raw["dependency_id"],
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                weight=EDGE_WEIGHTS[edge_type],
            )
        )

    return WeightedAssetGraph(
        assets=assets,
        edges=tuple(
            sorted(
                edges,
                key=lambda edge: (
                    edge.source_id,
                    edge.target_id,
                    edge.dependency_id,
                ),
            )
        ),
    )
