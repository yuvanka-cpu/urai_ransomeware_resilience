from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any

from config.ransomware.shared.identifier_contract import (
    IdentifierType,
    is_valid_identifier,
)
from config.ransomware.shared.source_event_contract import (
    is_valid_event_family,
    is_valid_source_system,
)
from config.ransomware.shared.zone_contract import is_valid_zone


REQUIRED_FIELDS = {
    "event_id",
    "event_time",
    "ingest_time",
    "schema_version",
    "source_system",
    "event_family",
    "event_type",
    "industry",
    "site_id",
    "asset_id",
    "zone",
    "severity",
    "attributes",
    "metrics",
    "quality_flags",
    "data_provenance",
    "payload_hash",
}

OPTIONAL_FIELDS = {"actor_id"}

ALLOWED_INDUSTRIES = {"energy", "petrochemical"}

ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

EXPECTED_FIELD_TYPES = {
    "event_id": str,
    "event_time": str,
    "ingest_time": str,
    "schema_version": str,
    "source_system": str,
    "event_family": str,
    "event_type": str,
    "industry": str,
    "site_id": str,
    "asset_id": str,
    "zone": str,
    "severity": str,
    "attributes": dict,
    "metrics": dict,
    "quality_flags": list,
    "data_provenance": str,
    "payload_hash": str,
}

HASHED_FIELDS = (
    "event_id",
    "event_time",
    "ingest_time",
    "schema_version",
    "source_system",
    "event_family",
    "event_type",
    "industry",
    "site_id",
    "asset_id",
    "zone",
    "actor_id",
    "severity",
    "attributes",
    "metrics",
    "quality_flags",
    "data_provenance",
)


def canonical_payload_hash(event: dict[str, Any]) -> str:
    """Return the deterministic SHA-256 hash of the canonical event payload."""

    payload = {
        field: event.get(field)
        for field in HASHED_FIELDS
    }

    for field in ("attributes", "metrics", "quality_flags"):
        value = payload[field]

        if isinstance(value, str):
            payload[field] = json.loads(value)

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def validate_event(event: dict[str, Any]) -> list[str]:
    """Return validation errors for one canonical observable event."""
    errors: list[str] = []

    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        errors.extend(
            f"missing required field: {field}"
            for field in sorted(missing)
        )

    unknown = set(event.keys()) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        errors.extend(
            f"unknown field: {field}"
            for field in sorted(unknown)
        )

    for field, expected_type in EXPECTED_FIELD_TYPES.items():
        if field not in event:
            continue

        if not isinstance(event[field], expected_type):
            errors.append(
                f"{field}: expected {expected_type.__name__}, "
                f"got {type(event[field]).__name__}"
            )

    if "actor_id" in event and event["actor_id"] is not None:
        if not isinstance(event["actor_id"], str):
            errors.append("actor_id: expected string or null")

    if (
        isinstance(event.get("event_id"), str)
        and not event["event_id"].strip()
    ):
        errors.append("event_id: must not be empty")

    if event.get("industry") not in ALLOWED_INDUSTRIES:
        errors.append("industry: invalid canonical industry")

    if event.get("severity") not in ALLOWED_SEVERITIES:
        errors.append("severity: invalid canonical severity")

    if event.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            "schema_version: unsupported canonical schema version"
        )

    if isinstance(event.get("payload_hash"), str):
        payload_hash = event["payload_hash"]

        if not re.fullmatch(
            r"[0-9a-fA-F]{64}",
            payload_hash,
        ):
            errors.append(
                "payload_hash: expected SHA-256 hexadecimal digest"
            )
        else:
            expected_hash = canonical_payload_hash(event)

            if payload_hash.lower() != expected_hash:
                errors.append(
                    "payload_hash: does not match canonical payload"
                )

    if (
        isinstance(event.get("data_provenance"), str)
        and not event["data_provenance"].strip()
    ):
        errors.append("data_provenance: must not be empty")

    if (
        isinstance(event.get("source_system"), str)
        and not is_valid_source_system(event["source_system"])
    ):
        errors.append("source_system: invalid canonical source system")

    if (
        isinstance(event.get("event_family"), str)
        and not is_valid_event_family(event["event_family"])
    ):
        errors.append("event_family: invalid canonical event family")

    if (
        isinstance(event.get("zone"), str)
        and not is_valid_zone(event["zone"])
    ):
        errors.append("zone: invalid canonical zone")

    if (
        isinstance(event.get("site_id"), str)
        and not is_valid_identifier(
            event["site_id"],
            IdentifierType.SITE,
        )
    ):
        errors.append("site_id: invalid canonical identifier")

    if (
        isinstance(event.get("asset_id"), str)
        and not is_valid_identifier(
            event["asset_id"],
            IdentifierType.ASSET,
        )
    ):
        errors.append("asset_id: invalid canonical identifier")

    if (
        isinstance(event.get("site_id"), str)
        and isinstance(event.get("asset_id"), str)
        and event["site_id"].split("-", 1)[0]
        != event["asset_id"].split("-", 1)[0]
    ):
        errors.append(
            "site_id and asset_id: industry prefix mismatch"
        )

    for field in ("event_time", "ingest_time"):
        if field in event and isinstance(event[field], str):
            try:
                parsed = datetime.fromisoformat(
                    event[field].replace("Z", "+00:00")
                )

                if (
                    event[field][-1:] != "Z"
                    or parsed.utcoffset() is None
                    or parsed.utcoffset().total_seconds() != 0
                ):
                    errors.append(
                        f"{field}: timestamp must be canonical UTC"
                    )

            except ValueError:
                errors.append(f"{field}: invalid timestamp")

    if (
        "attributes" in event
        and isinstance(event["attributes"], dict)
    ):
        for key, value in event["attributes"].items():
            if not isinstance(key, str) or not isinstance(value, str):
                errors.append(
                    "attributes: keys and values must be strings"
                )

    if (
        "metrics" in event
        and isinstance(event["metrics"], dict)
    ):
        for key, value in event["metrics"].items():
            if (
                not isinstance(key, str)
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                errors.append(
                    "metrics: keys must be strings and values numeric"
                )

    if (
        "quality_flags" in event
        and isinstance(event["quality_flags"], list)
    ):
        if not all(
            isinstance(flag, str)
            for flag in event["quality_flags"]
        ):
            errors.append(
                "quality_flags: every value must be a string"
            )

    return errors