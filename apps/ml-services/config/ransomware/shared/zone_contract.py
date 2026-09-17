from enum import Enum


class Zone(str, Enum):
    ENTERPRISE_IT = "enterprise_it"
    INDUSTRIAL_DMZ = "industrial_dmz"
    OPERATIONS_SUPPORT = "operations_support"
    SUPERVISORY_CONTROL = "supervisory_control"
    FIELD_CONTROL = "field_control"
    PROTECTION_SAFETY = "protection_safety"


ALLOWED_ZONES = {zone.value for zone in Zone}


def is_valid_zone(zone: str) -> bool:
    """Return True when the zone is one of the six canonical zones."""
    return zone in ALLOWED_ZONES
