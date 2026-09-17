from enum import Enum


class ProtectedNodeType(str, Enum):
    RELAY = "relay"
    RTU = "rtu"
    IED = "ied"
    PLC = "plc"
    SIS = "sis"
    ESD = "esd"
    INTERLOCK = "interlock"
    SAFETY_CONTROLLER = "safety_controller"


class AccessMode(str, Enum):
    READ_ONLY = "read_only"


ALLOWED_PROTECTED_NODE_TYPES = {
    node_type.value for node_type in ProtectedNodeType
}


def is_valid_protected_node_type(node_type: str) -> bool:
    """Return True when the node type is a canonical protected type."""
    return node_type in ALLOWED_PROTECTED_NODE_TYPES


def is_read_only_access(access_mode: str) -> bool:
    """Return True only for the protected read-only access mode."""
    return access_mode == AccessMode.READ_ONLY.value
