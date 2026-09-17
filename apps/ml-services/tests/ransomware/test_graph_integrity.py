import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
)


def load_assets(sector):
    asset_file = CONFIG_ROOT / sector / "assets.json"
    return json.loads(
        asset_file.read_text(encoding="utf-8")
    )["assets"]


def load_edges(sector):
    edge_file = CONFIG_ROOT / sector / "graph_edges.json"
    return json.loads(
        edge_file.read_text(encoding="utf-8")
    )["edges"]


def test_no_cross_sector_edges():
    energy_edges = load_edges("energy")
    petrochemical_edges = load_edges("petrochemical")

    for edge in energy_edges:
        assert edge["source_id"].startswith("energy-")
        assert edge["target_id"].startswith("energy-")

    for edge in petrochemical_edges:
        assert edge["source_id"].startswith("petrochemical-")
        assert edge["target_id"].startswith("petrochemical-")


def test_all_canonical_assets_have_graph_membership():
    for sector in ("energy", "petrochemical"):
        assets = load_assets(sector)
        edges = load_edges(sector)

        asset_ids = {asset["asset_id"] for asset in assets}
        graph_ids = {
            edge["source_id"] for edge in edges
        } | {
            edge["target_id"] for edge in edges
        }

        assert asset_ids == graph_ids


def test_protected_assets_are_not_directly_reached_from_enterprise_it():
    for sector in ("energy", "petrochemical"):
        assets = load_assets(sector)
        edges = load_edges(sector)

        zones = {
            asset["asset_id"]: asset["zone"]
            for asset in assets
        }

        for edge in edges:
            source_zone = zones[edge["source_id"]]
            target_zone = zones[edge["target_id"]]

            if source_zone == "enterprise_it":
                assert target_zone != "protection_safety"
