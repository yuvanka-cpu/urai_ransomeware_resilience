import json
from pathlib import Path

from config.ransomware.shared.graph_contract import is_valid_edge_type


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
)


def load_assets():
    asset_file = CONFIG_ROOT / "energy" / "assets.json"
    return json.loads(
        asset_file.read_text(encoding="utf-8")
    )["assets"]


def load_edges():
    edge_file = CONFIG_ROOT / "energy" / "graph_edges.json"
    return json.loads(
        edge_file.read_text(encoding="utf-8")
    )["edges"]


def test_energy_graph_edges_are_valid():
    assets = load_assets()
    edges = load_edges()

    asset_ids = {asset["asset_id"] for asset in assets}

    assert edges

    for edge in edges:
        assert edge["dependency_id"]
        assert edge["source_id"] in asset_ids
        assert edge["target_id"] in asset_ids
        assert is_valid_edge_type(edge["edge_type"])


def test_energy_graph_dependency_ids_are_unique():
    edges = load_edges()

    dependency_ids = [
        edge["dependency_id"]
        for edge in edges
    ]

    assert len(dependency_ids) == len(set(dependency_ids))


def test_energy_graph_has_no_self_referencing_edges():
    edges = load_edges()

    for edge in edges:
        assert edge["source_id"] != edge["target_id"]
