from enum import Enum


class EdgeType(str, Enum):
    NETWORK_REACHABILITY = "network_reachability"
    IDENTITY_TRUST = "identity_trust"
    SERVICE_DEPENDENCY = "service_dependency"
    DATA_FLOW = "data_flow"
    BACKUP_COVERAGE = "backup_coverage"
    RECOVERY_PREREQUISITE = "recovery_prerequisite"


ALLOWED_EDGE_TYPES = {edge.value for edge in EdgeType}


def is_valid_edge_type(edge_type: str) -> bool:
    """Return True when the edge type is one of the six canonical types."""
    return edge_type in ALLOWED_EDGE_TYPES

