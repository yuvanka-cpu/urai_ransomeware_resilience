from config.ransomware.graph_propagation import (
    EDGE_WEIGHTS,
    load_sector_graph,
)


def test_energy_graph_loads_and_uses_canonical_edges():
    graph = load_sector_graph("energy")

    assert len(graph.assets) == 10
    assert len(graph.edges) == 9

    for edge in graph.edges:
        assert edge.edge_type in EDGE_WEIGHTS
        assert 0.0 < edge.weight <= 1.0


def test_petrochemical_graph_loads_and_uses_canonical_edges():
    graph = load_sector_graph("petrochemical")

    assert len(graph.assets) == 11
    assert len(graph.edges) == 11

    for edge in graph.edges:
        assert edge.edge_type in EDGE_WEIGHTS
        assert 0.0 < edge.weight <= 1.0


def test_energy_propagation_is_deterministic_and_preserves_path():
    graph = load_sector_graph("energy")

    seed = "energy-blr01-asset-identity-001"

    first = graph.propagate([seed])
    second = graph.propagate([seed])

    assert first == second
    assert first[0].asset_id == seed
    assert first[0].score == 1.0
    assert first[0].hops == 0
    assert first[0].path == (seed,)
    assert first[0].edge_types == ()

    target = "energy-blr01-asset-industrial-dmz-001"
    target_result = next(
        result for result in first if result.asset_id == target
    )

    assert target_result.hops == 2
    assert target_result.path == (
        seed,
        "energy-blr01-asset-vpn-001",
        target,
    )
    assert target_result.edge_types == (
        "identity_trust",
        "network_reachability",
    )


def test_propagation_does_not_cycle():
    graph = load_sector_graph("petrochemical")

    seed = "petrochemical-mng01-asset-identity-001"
    results = graph.propagate([seed])

    for result in results:
        assert len(result.path) == len(set(result.path))
        assert result.hops == len(result.path) - 1


def test_unknown_seed_is_rejected():
    graph = load_sector_graph("energy")

    try:
        graph.propagate(["does-not-exist"])
    except ValueError as exc:
        assert "Unknown seed assets" in str(exc)
    else:
        raise AssertionError("Unknown seed asset was accepted")


def test_empty_seed_returns_no_results():
    graph = load_sector_graph("energy")

    assert graph.propagate([]) == []
