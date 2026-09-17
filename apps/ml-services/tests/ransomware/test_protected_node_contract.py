from config.ransomware.shared.protected_node_contract import (
    AccessMode,
    ProtectedNodeType,
    is_read_only_access,
    is_valid_protected_node_type,
)


def test_protected_node_types_are_exact():
    expected = {
        "relay",
        "rtu",
        "ied",
        "plc",
        "sis",
        "esd",
        "interlock",
        "safety_controller",
    }

    actual = {
        node_type.value
        for node_type in ProtectedNodeType
    }

    assert actual == expected


def test_all_protected_node_types_are_valid():
    for node_type in ProtectedNodeType:
        assert is_valid_protected_node_type(node_type.value)


def test_only_read_only_access_is_allowed():
    assert is_read_only_access(AccessMode.READ_ONLY.value)

    assert not is_read_only_access("write")
    assert not is_read_only_access("read_write")
    assert not is_read_only_access("control")
