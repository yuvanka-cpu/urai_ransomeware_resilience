import torch

from config.ransomware.graph_challengers import (
    GATv2,
    GraphSAGE,
    build_node_features,
    build_sample,
    load_sector_graph,
)


def test_graphsage_and_gatv2_forward():
    graph = load_sector_graph("energy")
    seed = {sorted(graph.assets)[0]}

    _, features = build_node_features(graph, seed)

    edges = torch.tensor(
        [
            [0, 1],
            [1, 2],
        ],
        dtype=torch.long,
    )

    graphsage = GraphSAGE(features.shape[1])
    gatv2 = GATv2(features.shape[1])

    assert graphsage(features, edges).shape == (features.shape[0],)
    assert gatv2(features, edges).shape == (features.shape[0],)


def test_models_have_same_input_contract():
    energy = load_sector_graph("energy")
    petrochemical = load_sector_graph("petrochemical")

    _, energy_features = build_node_features(
        energy,
        {sorted(energy.assets)[0]},
    )

    _, petrochemical_features = build_node_features(
        petrochemical,
        {sorted(petrochemical.assets)[0]},
    )

    assert energy_features.shape[1] > 0
    assert petrochemical_features.shape[1] > 0


def test_unseen_node_feature_contract_does_not_use_truth():
    graph = load_sector_graph("energy")
    unseen = sorted(graph.assets)[-1]

    _, features_without_seed = build_node_features(
        graph,
        set(),
    )

    _, features_with_seed = build_node_features(
        graph,
        {unseen},
    )

    assert features_without_seed.shape == features_with_seed.shape
    assert torch.all(
        features_without_seed[:, :-1]
        == features_with_seed[:, :-1]
    )


def test_sample_labels_are_evaluation_only():
    graph = load_sector_graph("petrochemical")
    node_ids = sorted(graph.assets)

    sample = build_sample(
        graph,
        {node_ids[0]},
        {node_ids[-1]},
    )

    assert sample.labels.sum().item() == 1
    assert sample.labels.shape[0] == len(node_ids)
    assert sample.features.shape[0] == len(node_ids)
