from enum import Enum


class SourceSystem(str, Enum):
    ENDPOINT = "endpoint"
    FILE = "file"
    IDENTITY = "identity"
    NETWORK = "network"
    BACKUP = "backup"
    SERVICE_HEALTH = "service_health"
    ASSET = "asset"
    MAINTENANCE = "maintenance"
    SYNTHETIC = "synthetic"


class EventFamily(str, Enum):
    ENDPOINT = "endpoint"
    FILE = "file"
    IDENTITY = "identity"
    NETWORK = "network"
    BACKUP = "backup"
    SERVICE_HEALTH = "service_health"
    ASSET = "asset"
    MAINTENANCE = "maintenance"
    SYNTHETIC = "synthetic"


ALLOWED_SOURCE_SYSTEMS = {
    source.value for source in SourceSystem
}

ALLOWED_EVENT_FAMILIES = {
    family.value for family in EventFamily
}


def is_valid_source_system(source_system: str) -> bool:
    """Return True when the source system is registered."""
    return source_system in ALLOWED_SOURCE_SYSTEMS


def is_valid_event_family(event_family: str) -> bool:
    """Return True when the event family is registered."""
    return event_family in ALLOWED_EVENT_FAMILIES
