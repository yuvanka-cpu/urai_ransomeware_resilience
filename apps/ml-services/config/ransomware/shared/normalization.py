from datetime import datetime, timezone
import ipaddress
import re
from typing import Any


NULL_SENTINELS = {"", "null", "none", "n/a", "na", "unknown", "-"}


def normalize_timestamp(value: Any) -> str:
    """Normalize a timestamp to UTC ISO-8601 representation."""
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("invalid timestamp")

    if timestamp.tzinfo is None:
        raise ValueError("timestamp must include timezone")

    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_number(value: Any) -> float:
    """Normalize a numeric value without silently converting invalid input."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid number") from exc


def normalize_boolean(value: Any) -> bool:
    """Normalize common boolean representations."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes", "y"}:
            return True

        if normalized in {"false", "0", "no", "n"}:
            return False

    if isinstance(value, int) and value in {0, 1}:
        return bool(value)

    raise ValueError("invalid boolean")


def normalize_enum(value: Any, allowed_values: set[str]) -> str:
    """Normalize a registered enum value."""
    if not isinstance(value, str):
        raise ValueError("enum value must be a string")

    normalized = value.strip().lower()

    if normalized not in allowed_values:
        raise ValueError("invalid enum value")

    return normalized


def normalize_ip(value: Any) -> str:
    """Normalize an IPv4 or IPv6 address."""
    try:
        return str(ipaddress.ip_address(str(value).strip()))
    except ValueError as exc:
        raise ValueError("invalid IP address") from exc


def normalize_identifier(value: Any) -> str:
    """Normalize an identifier while preserving its canonical value."""
    if not isinstance(value, str):
        raise ValueError("identifier must be a string")

    normalized = value.strip().lower()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", normalized):
        raise ValueError("invalid identifier")

    return normalized


def normalize_hash(value: Any) -> str:
    """Normalize a hexadecimal hash representation."""
    if not isinstance(value, str):
        raise ValueError("hash must be a string")

    normalized = value.strip().lower()

    if not re.fullmatch(r"[0-9a-f]+", normalized):
        raise ValueError("invalid hash")

    return normalized


def normalize_list(value: Any) -> list[Any]:
    """Normalize a list or a comma-separated string into a list."""
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]

    raise ValueError("invalid list")


def normalize_nested_record(value: Any) -> dict[str, Any]:
    """Normalize a nested record without changing its structure."""
    if not isinstance(value, dict):
        raise ValueError("nested record must be an object")

    return dict(value)


def normalize_null_or_sentinel(value: Any) -> Any:
    """Convert declared null/sentinel values to None."""
    if value is None:
        return None

    if isinstance(value, str) and value.strip().lower() in NULL_SENTINELS:
        return None

    return value


def normalize_unit(value: Any, declared_unit: str) -> tuple[float, str]:
    """Normalize a numeric value while retaining its declared unit."""
    if not declared_unit or not isinstance(declared_unit, str):
        raise ValueError("declared unit is required")

    return normalize_number(value), declared_unit.strip()
