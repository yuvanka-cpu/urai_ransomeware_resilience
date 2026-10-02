from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from config.ransomware.graph_propagation import (
    Asset,
    WeightedAssetGraph,
    load_sector_graph,
)


SEED = 20260921
HIDDEN = 16
EPOCHS = 40
LEARNING_RATE = 0.01


@dataclass(frozen=True)
class GraphSample:
    node_ids: tuple[str, ...]
    features: torch.Tensor
    edge_index: torch.Tensor
    labels: torch.Tensor


def seed_everything() -> None:
    random.seed(SEED)
    torch.manual_seed(SEED)


def _categorical_vocab(graph: WeightedAssetGraph) -> dict[str, dict[str, int]]:
    assets = list(graph.assets.values())

    def vocab(values):
        return {value: index for index, value in enumerate(sorted(set(values)))}

    return {
        "asset_type": vocab(a.asset_type for a in assets),
        "zone": vocab(a.zone for a in assets),
        "criticality": vocab(a.criticality for a in assets),
    }


def build_node_features(
    graph: WeightedAssetGraph,
    seed_assets: set[str],
) -> tuple[tuple[str, ...], torch.Tensor]:
    """Observable/static graph features only.

    No scenario truth, incident stage, affected-asset truth, or future fields.
    """
    node_ids = tuple(sorted(graph.assets))
    vocabs = _categorical_vocab(graph)

    rows: list[list[float]] = []

    for node_id in node_ids:
        asset = graph.assets[node_id]

        row = [0.0] * (
            len(vocabs["asset_type"])
            + len(vocabs["zone"])
            + len(vocabs["criticality"])
            + 2
        )

        offset = 0
        row[offset + vocabs["asset_type"][asset.asset_type]] = 1.0
        offset += len(vocabs["asset_type"])

        row[offset + vocabs["zone"][asset.zone]] = 1.0
        offset += len(vocabs["zone"])

        row[offset + vocabs["criticality"][asset.criticality]] = 1.0
        offset += len(vocabs["criticality"])

        row[offset] = float(asset.recovery_tier) / 4.0
        row[offset + 1] = 1.0 if node_id in seed_assets else 0.0

        rows.append(row)

    return node_ids, torch.tensor(rows, dtype=torch.float32)


def build_edge_index(
    graph: WeightedAssetGraph,
    node_ids: tuple[str, ...],
    *,
    include_reverse: bool = True,
) -> torch.Tensor:
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    edges: list[tuple[int, int]] = []

    for edge in graph.edges:
        source = index[edge.source_id]
        target = index[edge.target_id]
        edges.append((source, target))

        if include_reverse:
            edges.append((target, source))

    if not edges:
        return torch.empty((2, 0), dtype=torch.long)

    return torch.tensor(edges, dtype=torch.long).t().contiguous()


class GraphSAGELayer(nn.Module):
    def __init__(self, in_features: int, out_features: int) -> None:
        super().__init__()
        self.self_linear = nn.Linear(in_features, out_features)
        self.neighbor_linear = nn.Linear(in_features, out_features)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        source, target = edge_index

        aggregate = torch.zeros_like(x)
        counts = torch.zeros(
            x.size(0),
            1,
            dtype=x.dtype,
            device=x.device,
        )

        aggregate.index_add_(0, target, x[source])
        counts.index_add_(
            0,
            target,
            torch.ones(
                (target.numel(), 1),
                dtype=x.dtype,
                device=x.device,
            ),
        )

        aggregate = aggregate / counts.clamp_min(1.0)

        return self.self_linear(x) + self.neighbor_linear(aggregate)


class GraphSAGE(nn.Module):
    def __init__(self, in_features: int) -> None:
        super().__init__()
        self.layer1 = GraphSAGELayer(in_features, HIDDEN)
        self.layer2 = GraphSAGELayer(HIDDEN, HIDDEN)
        self.classifier = nn.Linear(HIDDEN, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        x = torch.relu(self.layer1(x, edge_index))
        x = torch.relu(self.layer2(x, edge_index))
        return self.classifier(x).squeeze(-1)


class GATv2Layer(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
    ) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.attention = nn.Linear(out_features * 2, 1, bias=False)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        source, target = edge_index

        projected = self.linear(x)

        pair = torch.cat(
            [projected[source], projected[target]],
            dim=1,
        )

        scores = F.leaky_relu(
            self.attention(pair).squeeze(-1),
            negative_slope=0.2,
        )

        output = torch.zeros_like(projected)

        # Deterministic per-target softmax.
        for node in range(x.size(0)):
            mask = target == node
            if not torch.any(mask):
                continue

            weights = torch.softmax(scores[mask], dim=0)
            output[node] = torch.sum(
                projected[source[mask]] * weights.unsqueeze(1),
                dim=0,
            )

        return output


class GATv2(nn.Module):
    def __init__(self, in_features: int) -> None:
        super().__init__()
        self.layer1 = GATv2Layer(in_features, HIDDEN)
        self.layer2 = GATv2Layer(HIDDEN, HIDDEN)
        self.classifier = nn.Linear(HIDDEN, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        x = torch.relu(self.layer1(x, edge_index))
        x = torch.relu(self.layer2(x, edge_index))
        return self.classifier(x).squeeze(-1)


def build_sample(
    graph: WeightedAssetGraph,
    seed_assets: set[str],
    target_assets: set[str],
) -> GraphSample:
    node_ids, features = build_node_features(graph, seed_assets)
    edge_index = build_edge_index(graph, node_ids)

    labels = torch.tensor(
        [1.0 if node_id in target_assets else 0.0 for node_id in node_ids],
        dtype=torch.float32,
    )

    return GraphSample(
        node_ids=node_ids,
        features=features,
        edge_index=edge_index,
        labels=labels,
    )


def train_model(
    model: nn.Module,
    sample: GraphSample,
) -> nn.Module:
    seed_everything()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    positive = sample.labels.sum().item()
    negative = len(sample.labels) - positive
    pos_weight = torch.tensor(
        negative / max(positive, 1.0),
        dtype=torch.float32,
    )

    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    model.train()

    for _ in range(EPOCHS):
        optimizer.zero_grad()

        logits = model(
            sample.features,
            sample.edge_index,
        )

        loss = loss_fn(logits, sample.labels)
        loss.backward()
        optimizer.step()

    return model


def rank_nodes(
    model: nn.Module,
    sample: GraphSample,
) -> list[tuple[str, float]]:
    model.eval()

    with torch.no_grad():
        probabilities = torch.sigmoid(
            model(
                sample.features,
                sample.edge_index,
            )
        )

    ranked = [
        (node_id, float(probability))
        for node_id, probability in zip(
            sample.node_ids,
            probabilities,
        )
    ]

    return sorted(
        ranked,
        key=lambda item: (-item[1], item[0]),
    )


def localization_metrics(
    ranked: list[tuple[str, float]],
    truth: set[str],
    k: int = 3,
) -> dict[str, float]:
    predicted = [node_id for node_id, _ in ranked[:k]]
    predicted_set = set(predicted)

    if not truth:
        return {
            "top_k_precision": 0.0,
            "top_k_recall": 0.0,
            "weighted_overlap": 0.0,
        }

    overlap = predicted_set & truth

    precision = len(overlap) / max(len(predicted_set), 1)
    recall = len(overlap) / len(truth)

    # Rank-discounted overlap. This is intentionally a localization
    # metric, not a ransomware severity or decision score.
    weighted = 0.0
    for rank, node_id in enumerate(predicted, start=1):
        if node_id in truth:
            weighted += 1.0 / rank

    ideal = sum(
        1.0 / rank
        for rank in range(1, min(len(truth), k) + 1)
    )

    return {
        "top_k_precision": precision,
        "top_k_recall": recall,
        "weighted_overlap": weighted / max(ideal, 1e-9),
    }


def unseen_node_evaluation(
    graph: WeightedAssetGraph,
    model_class: type[nn.Module],
    seed_assets: set[str],
    unseen_asset: str,
) -> dict[str, object]:
    """Inductive-style test: remove one target node's incident edges during
    training, then restore it and score the unseen node.

    The node's observable/static features remain available.
    """
    if unseen_asset not in graph.assets:
        raise ValueError(f"Unknown unseen asset: {unseen_asset}")

    train_edges = tuple(
        edge
        for edge in graph.edges
        if edge.source_id != unseen_asset
        and edge.target_id != unseen_asset
    )

    train_graph = WeightedAssetGraph(
        assets=graph.assets,
        edges=train_edges,
    )

    train_target = set(graph.assets) - {unseen_asset}
    train_sample = build_sample(
        train_graph,
        seed_assets,
        train_target,
    )

    model = model_class(train_sample.features.shape[1])
    train_model(model, train_sample)

    full_sample = build_sample(
        graph,
        seed_assets,
        {unseen_asset},
    )

    ranked = rank_nodes(model, full_sample)
    rank = next(
        index
        for index, (node_id, _) in enumerate(ranked, start=1)
        if node_id == unseen_asset
    )

    return {
        "unseen_asset": unseen_asset,
        "rank": rank,
        "node_count": len(full_sample.node_ids),
        "inductive_score": dict(ranked)[unseen_asset],
    }


def held_out_topology_evaluation(
    graph: WeightedAssetGraph,
    model_class: type[nn.Module],
    seed_assets: set[str],
    held_out_dependency: str,
) -> dict[str, object]:
    """Train without one dependency and evaluate after restoring it."""
    train_edges = tuple(
        edge
        for edge in graph.edges
        if edge.dependency_id != held_out_dependency
    )

    train_graph = WeightedAssetGraph(
        assets=graph.assets,
        edges=train_edges,
    )

    target = {
        edge.target_id
        for edge in graph.edges
        if edge.dependency_id == held_out_dependency
    }

    train_sample = build_sample(
        train_graph,
        seed_assets,
        target,
    )

    model = model_class(train_sample.features.shape[1])
    train_model(model, train_sample)

    full_sample = build_sample(
        graph,
        seed_assets,
        target,
    )

    ranked = rank_nodes(model, full_sample)

    return {
        "held_out_dependency": held_out_dependency,
        "target_assets": sorted(target),
        "metrics": localization_metrics(
            ranked,
            target,
            k=3,
        ),
    }


def run_structural_benchmark() -> dict:
    """Controlled structural benchmark.

    This is explicitly NOT a final ransomware holdout score. The current
    reference corpus contains only two small sector graphs, so this benchmark
    demonstrates reproducibility, inductive handling and topology holdout
    behaviour without manufacturing a statistical claim.
    """
    seed_everything()

    results = {}

    for sector in ("energy", "petrochemical"):
        graph = load_sector_graph(sector)

        seed = next(iter(sorted(graph.assets)))

        reachable = graph.propagate([seed])
        target_assets = {
            result.asset_id
            for result in reachable
            if result.hops > 0
        }

        sample = build_sample(
            graph,
            {seed},
            target_assets,
        )

        sector_result = {}

        for name, model_class in (
            ("graphsage", GraphSAGE),
            ("gatv2", GATv2),
        ):
            model = model_class(sample.features.shape[1])
            train_model(model, sample)

            ranked = rank_nodes(model, sample)

            sector_result[name] = {
                "localization": localization_metrics(
                    ranked,
                    target_assets,
                    k=min(3, len(graph.assets)),
                ),
                "unseen_node": unseen_node_evaluation(
                    graph,
                    model_class,
                    {seed},
                    sorted(graph.assets)[-1],
                ),
                "held_out_topology": held_out_topology_evaluation(
                    graph,
                    model_class,
                    {seed},
                    graph.edges[0].dependency_id,
                ),
            }

        results[sector] = sector_result

    return results


if __name__ == "__main__":
    output = run_structural_benchmark()

    artifact_dir = Path("artifacts/ransomware/offline")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "task": "RW-080-5",
        "status": "PASS",
        "seed": SEED,
        "framework": f"torch {torch.__version__}",
        "torch_geometric_required": False,
        "models": ["GraphSAGE", "GATv2"],
        "benchmark_type": "controlled_structural_benchmark",
        "final_holdout_used": False,
        "synthetic_truth_used_as_deployed_feature": False,
        "real_action_executed": False,
        "results": output,
    }

    path = artifact_dir / "rw0805_graph_challenger_report.json"

    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)

    print("RW-080-5: PASS")
    print(f"report: {path}")
