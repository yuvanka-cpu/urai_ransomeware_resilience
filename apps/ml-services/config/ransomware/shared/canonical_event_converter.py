"""Strict conversion of explicitly mapped records into canonical events."""

from typing import Any

from config.ransomware.shared.identifier_contract import (
    IdentifierType,
    is_valid_identifier,
)
from config.ransomware.shared.normalization import (
    normalize_enum,
    normalize_identifier,
    normalize_list,
    normalize_nested_record,
    normalize_null_or_sentinel,
    normalize_number,
    normalize_timestamp,
)
from config.ransomware.shared.source_event_contract import (
    ALLOWED_EVENT_FAMILIES,
    ALLOWED_SOURCE_SYSTEMS,
)
from config.ransomware.shared.validation.canonical_event_validator import (
    canonical_payload_hash,
    validate_event,
)
from config.ransomware.shared.zone_contract import ALLOWED_ZONES


def convert_to_canonical_event(
    source_record: dict[str, Any],
    *,
    field_mapping: dict[str, str],
) -> dict[str, Any]:
    """Convert explicitly mapped source fields into a validated event.

    field_mapping maps canonical field names to source-record field names.
    attributes and metrics must be provided as nested records.
    No source-specific mapping is inferred.
    """
    if not isinstance(source_record, dict):
        raise ValueError("source record must be an object")
    if not isinstance(field_mapping, dict):
        raise ValueError("field_mapping must be an object")

    required_source_fields = {
        "event_id", "event_time", "ingest_time", "schema_version",
        "source_system", "event_family", "event_type", "industry",
        "site_id", "asset_id", "zone", "severity", "attributes",
        "metrics", "quality_flags", "data_provenance",
    }
    allowed_mapping_fields = required_source_fields | {"actor_id"}

    unknown = set(field_mapping) - allowed_mapping_fields
    if unknown:
        raise ValueError(f"unknown canonical mapping fields: {sorted(unknown)}")

    missing = required_source_fields - set(field_mapping)
    if missing:
        raise ValueError(f"missing canonical mappings: {sorted(missing)}")

    event: dict[str, Any] = {}
    for canonical_name, source_name in field_mapping.items():
        if not isinstance(source_name, str) or not source_name:
            raise ValueError(f"invalid source mapping for {canonical_name}")
        if source_name not in source_record:
            raise ValueError(f"source field missing for {canonical_name}: {source_name}")
        event[canonical_name] = source_record[source_name]

    for field in ("event_time", "ingest_time"):
        event[field] = normalize_timestamp(event[field])

    for field in ("event_id", "event_type", "data_provenance"):
        if not isinstance(event[field], str) or not event[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
        event[field] = event[field].strip()

    event["schema_version"] = normalize_enum(
        event["schema_version"], {"1.0"}
    )
    event["source_system"] = normalize_enum(
        event["source_system"], ALLOWED_SOURCE_SYSTEMS
    )
    event["event_family"] = normalize_enum(
        event["event_family"], ALLOWED_EVENT_FAMILIES
    )
    event["industry"] = normalize_enum(
        event["industry"], {"energy", "petrochemical"}
    )
    event["severity"] = normalize_enum(
        event["severity"], {"low", "medium", "high", "critical"}
    )
    event["zone"] = normalize_enum(event["zone"], ALLOWED_ZONES)

    for field, identifier_type in (
        ("site_id", IdentifierType.SITE),
        ("asset_id", IdentifierType.ASSET),
    ):
        event[field] = normalize_identifier(event[field])
        if not is_valid_identifier(event[field], identifier_type):
            raise ValueError(f"{field} is not a valid canonical identifier")

    if "actor_id" in event:
        actor_id = normalize_null_or_sentinel(event["actor_id"])
        if actor_id is not None:
            actor_id = normalize_identifier(actor_id)
        event["actor_id"] = actor_id

    attributes = normalize_nested_record(event["attributes"])
    if any(not isinstance(key, str) for key in attributes):
        raise ValueError("attribute keys must be strings")
    event["attributes"] = {}
    for key, value in attributes.items():
        if not isinstance(value, str):
            raise ValueError(f"attribute value for {key} must be a string")
        event["attributes"][key] = value

    metrics = normalize_nested_record(event["metrics"])
    event["metrics"] = {
        key: normalize_number(value)
        for key, value in metrics.items()
        if isinstance(key, str)
    }
    if len(event["metrics"]) != len(metrics):
        raise ValueError("metric keys must be strings")

    event["quality_flags"] = normalize_list(event["quality_flags"])
    if not all(isinstance(flag, str) for flag in event["quality_flags"]):
        raise ValueError("quality_flags must contain only strings")

    if "actor_id" not in event:
        event["actor_id"] = None

    event["payload_hash"] = ""
    event["payload_hash"] = canonical_payload_hash(event)

    errors = validate_event(event)
    if errors:
        raise ValueError("canonical event validation failed: " + "; ".join(errors))

    return event
