"""Validate synthetic observable timeline evidence before dashboard exposure."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from math import isfinite
from typing import Any


FORBIDDEN_KEYS = {
    "ground_truth",
    "ground_truth_label",
    "synthetic_truth",
    "truth_label",
    "is_ransomware",
    "incident_stage_truth",
    "affected_asset_truth",
    "blast_radius_truth",
    "analyst_disposition",
}

EXPECTED_SCOPE = "offline_synthetic_observable_evidence"


def contains_truth(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).strip().lower() in FORBIDDEN_KEYS
            or contains_truth(child)
            for key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(contains_truth(item) for item in value)
    return False


def valid_attributes(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, list):
        return all(valid_attributes(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and valid_attributes(item)
            for key, item in value.items()
        )
    return False


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def valid_timeline_evidence(body: dict[str, Any]) -> bool:
    if (
        not isinstance(body, dict)
        or body.get("status") != "available"
        or body.get("scope") != EXPECTED_SCOPE
        or body.get("data_provenance") != "synthetic_development"
        or body.get("is_operational_incident_timeline") is not False
        or contains_truth(body)
    ):
        return False

    events = body.get("timeline")
    count = body.get("event_count")

    if (
        not isinstance(events, list)
        or not events
        or type(count) is not int
        or count != len(events)
    ):
        return False

    previous_time = None
    assets = set()
    families = Counter()

    for expected_index, event in enumerate(events):
        if not isinstance(event, dict):
            return False

        if type(event.get("sequence_index")) is not int:
            return False
        if event["sequence_index"] != expected_index:
            return False

        timestamp = parse_timestamp(event.get("event_time"))
        if timestamp is None:
            return False

        if previous_time is not None and timestamp < previous_time:
            return False

        previous_time = timestamp

        for field in ("event_family", "event_type", "asset_id"):
            value = event.get(field)
            if not isinstance(value, str) or not value.strip():
                return False

        attributes = event.get("attributes")
        if not isinstance(attributes, dict):
            return False

        if not valid_attributes(attributes):
            return False

        assets.add(event["asset_id"])
        families[event["event_family"]] += 1

    if (
        parse_timestamp(body.get("first_event_at"))
        != parse_timestamp(events[0]["event_time"])
        or parse_timestamp(body.get("last_event_at"))
        != parse_timestamp(events[-1]["event_time"])
        or body.get("observed_asset_ids") != sorted(assets)
        or body.get("event_family_counts")
        != dict(sorted(families.items()))
    ):
        return False

    fingerprint = body.get("sequence_fingerprint_sha256")

    material = [
        {
            "sequence_index": event["sequence_index"],
            "event_family": event["event_family"],
            "event_type": event["event_type"],
            "asset_id": event["asset_id"],
            "attributes": event["attributes"],
        }
        for event in events
    ]

    try:
        canonical = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        expected_fingerprint = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError, OverflowError):
        return False

    if fingerprint != expected_fingerprint:
        return False

    if (
        not isinstance(fingerprint, str)
        or len(fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in fingerprint)
    ):
        return False

    for field in ("fingerprint_scope", "limitations"):
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    return True
