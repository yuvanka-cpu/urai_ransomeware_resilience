import json
from pathlib import Path

from config.ransomware.shared.graph_contract import is_valid_edge_type
from config.ransomware.shared.protected_node_contract import (
    is_read_only_access,
    is_valid_protected_node_type,
)
from config.ransomware.shared.zone_contract import is_valid_zone


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
)

def load_json(sector, filename):
    path = CONFIG_ROOT / sector / filename
    return json.loads(path.read_text(encoding="utf-8"))

def test_all_assets_have_valid_zones_and_sector_site_membership():
    for sector in ("energy", "petrochemical"):
        assets = load_json(sector, "assets.json")["assets"]

        for asset in assets:
            assert asset["asset_id"].startswith(f"{sector}-")
            assert asset["site_id"].startswith(f"{sector}-")
            assert is_valid_zone(asset["zone"])


def test_all_graph_edges_resolve_to_canonical_assets():
    for sector in ("energy", "petrochemical"):
        assets = load_json(sector, "assets.json")["assets"]
        edges = load_json(sector, "graph_edges.json")["edges"]

        asset_ids = {asset["asset_id"] for asset in assets}

        for edge in edges:
            assert edge["source_id"] in asset_ids
            assert edge["target_id"] in asset_ids
            assert is_valid_edge_type(edge["edge_type"])


def test_no_cross_sector_or_orphan_graph_references():
    energy_assets = {
        asset["asset_id"]
        for asset in load_json("energy", "assets.json")["assets"]
    }
    petrochemical_assets = {
        asset["asset_id"]
        for asset in load_json("petrochemical", "assets.json")["assets"]
    }

    for sector, own_assets, foreign_assets in (
        ("energy", energy_assets, petrochemical_assets),
        ("petrochemical", petrochemical_assets, energy_assets),
    ):
        edges = load_json(sector, "graph_edges.json")["edges"]

        for edge in edges:
            assert edge["source_id"] in own_assets
            assert edge["target_id"] in own_assets
            assert edge["source_id"] not in foreign_assets
            assert edge["target_id"] not in foreign_assets


def test_protected_nodes_remain_read_only_and_explicitly_bounded():
    for sector in ("energy", "petrochemical"):
        nodes = load_json(sector, "protected_nodes.json")["nodes"]

        for node in nodes:
            assert node["dependency_id"].startswith(f"{sector}-")
            assert node["node_id"].startswith(f"{sector}-")
            assert is_valid_protected_node_type(node["node_type"])
            assert is_read_only_access(node["access_mode"])
            assert node["protected_boundary"] is True


def test_no_enterprise_it_edge_directly_targets_protection_safety():
    for sector in ("energy", "petrochemical"):
        assets = load_json(sector, "assets.json")["assets"]
        edges = load_json(sector, "graph_edges.json")["edges"]

        zones = {
            asset["asset_id"]: asset["zone"]
            for asset in assets
        }

        for edge in edges:
            source_zone = zones[edge["source_id"]]
            target_zone = zones[edge["target_id"]]

            if source_zone == "enterprise_it":
                assert target_zone != "protection_safety"
