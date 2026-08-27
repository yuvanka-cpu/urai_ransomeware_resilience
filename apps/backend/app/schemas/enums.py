from enum import Enum


class Decision(str, Enum):
    NORMAL = "normal"
    INVESTIGATE = "investigate"
    HIGH_RISK = "high_risk"
    UNAVAILABLE = "unavailable"


class IncidentStage(str, Enum):
    NONE = "none"
    PRECURSOR = "precursor"
    CREDENTIAL_MISUSE = "credential_misuse"
    LATERAL_MOVEMENT = "lateral_movement"
    STAGING = "staging"
    ENCRYPTION_IMPACT = "encryption_impact"
    RECOVERY = "recovery"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DataProvenance(str, Enum):
    LIVE_MODEL = "LIVE_MODEL"
    SYNTHETIC_GROUND_TRUTH = "SYNTHETIC_GROUND_TRUTH"
    STATIC_SCENARIO_METADATA = "STATIC_SCENARIO_METADATA"
    DERIVED_BY_BACKEND = "DERIVED_BY_BACKEND"
    FALLBACK = "FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"
