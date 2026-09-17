import json
from pathlib import Path

from config.ransomware.shared.protected_node_contract import (
    is_read_only_access,
    is_valid_protected_node_type,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
)


def load_nodes(sector):
    node_file = CONFIG_ROOT / sector / "protected_nodes.json"
    return json.loads(
        node_file.read_text(encoding="utf-8")
    )["nodes"]


def test_protected_nodes_are_valid():
    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)

        assert len(nodes) == 8

        for node in nodes:
            assert node["dependency_id"]
            assert node["node_id"]
            assert is_valid_protected_node_type(node["node_type"])
            assert is_read_only_access(node["access_mode"])
            assert node["protected_boundary"] is True


def test_protected_dependency_ids_are_unique():
    all_dependency_ids = []

    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)
        all_dependency_ids.extend(
            node["dependency_id"]
            for node in nodes
        )

    assert len(all_dependency_ids) == len(set(all_dependency_ids))


def test_protected_node_ids_are_unique():
    all_node_ids = []

    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)
        all_node_ids.extend(
            node["node_id"]
            for node in nodes
        )

    assert len(all_node_ids) == len(set(all_node_ids))
