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


def load_nodes(sector):
    node_file = CONFIG_ROOT / sector / "protected_nodes.json"
    return json.loads(
        node_file.read_text(encoding="utf-8")
    )["nodes"]


def test_protected_nodes_are_sector_scoped():
    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)

        for node in nodes:
            assert node["node_id"].startswith(
                f"{sector}-"
            )
            assert node["dependency_id"].startswith(
                f"{sector}-"
            )


def test_protected_nodes_have_no_control_fields():
    forbidden_fields = {
        "command",
        "write_action",
        "control_action",
        "query_action",
        "isolation_action",
    }

    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)

        for node in nodes:
            assert forbidden_fields.isdisjoint(node.keys())


def test_protected_nodes_are_metadata_only():
    required_fields = {
        "dependency_id",
        "node_id",
        "node_type",
        "access_mode",
        "protected_boundary",
    }

    for sector in ("energy", "petrochemical"):
        nodes = load_nodes(sector)

        for node in nodes:
            assert set(node.keys()) == required_fields
