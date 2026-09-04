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


class Industry(str, Enum):
    ENERGY = "energy"
    PETROCHEMICAL = "petrochemical"


class SiteType(str, Enum):
    CONTROL_CENTRE = "control_centre"
    SUBSTATION = "substation"
    REFINERY = "refinery"
    PETROCHEMICAL_COMPLEX = "petrochemical_complex"


class RuntimeState(str, Enum):
    MOCKED = "mocked"
    LIVE_MODEL = "live_model"
    DEGRADED = "degraded"
    FALLBACK = "fallback"
    UNAVAILABLE = "unavailable"


class ArtifactStatus(str, Enum):
    LOADED = "loaded"
    MISSING = "missing"
    STALE = "stale"
    CORRUPT = "corrupt"
    INCOMPATIBLE = "incompatible"
    TIMEOUT = "timeout"


class AssetState(str, Enum):
    CONFIRMED_AFFECTED = "confirmed_affected"
    SUSPECTED = "suspected"
    POTENTIALLY_EXPOSED = "potentially_exposed"
    PROTECTED = "protected"
    UNKNOWN = "unknown"


class OperationalImpactStatus(str, Enum):
    NONE_OBSERVED = "none_observed"
    POTENTIAL_DEPENDENCY_IMPACT = "potential_dependency_impact"
    OBSERVED_SUPPORT_DEGRADATION = "observed_support_degradation"
    UNKNOWN = "unknown"


class DataProvenance(str, Enum):
    LIVE_MODEL = "LIVE_MODEL"
    SYNTHETIC_GROUND_TRUTH = "SYNTHETIC_GROUND_TRUTH"
    STATIC_SCENARIO_METADATA = "STATIC_SCENARIO_METADATA"
    DERIVED_BY_BACKEND = "DERIVED_BY_BACKEND"
    FALLBACK = "FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"
