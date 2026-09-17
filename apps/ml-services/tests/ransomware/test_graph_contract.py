from config.ransomware.shared.graph_contract import (
    ALLOWED_EDGE_TYPES,
    EdgeType,
    is_valid_edge_type,
)


def test_six_canonical_edge_types_exist():
    assert ALLOWED_EDGE_TYPES == {
        "network_reachability",
        "identity_trust",
        "service_dependency",
        "data_flow",
        "backup_coverage",
        "recovery_prerequisite",
    }


def test_all_edge_enum_values_are_valid():
    for edge_type in EdgeType:
        assert is_valid_edge_type(edge_type.value)


def test_invalid_edge_types_are_rejected():
    assert not is_valid_edge_type("unknown")
    assert not is_valid_edge_type("network")
    assert not is_valid_edge_type("")
