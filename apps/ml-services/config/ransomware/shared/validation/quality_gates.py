from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


QUALITY_THRESHOLDS = {
    "schema_validity": 1.0,
    "required_context": 1.0,
    "timestamp_parse_success": 0.995,
    "known_asset_resolution": 0.99,
    "duplicate_event_id": 0.0,
}


REQUIRED_CONTEXT_FIELDS = {
    "industry",
    "site_id",
    "asset_id",
    "zone",
}


def load_known_assets(config_root: Path) -> dict[str, set[str]]:
    """Load authoritative asset IDs grouped by canonical industry."""
    known_assets: dict[str, set[str]] = {}

    for industry in ("energy", "petrochemical"):
        path = config_root / industry / "assets.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        known_assets[industry] = {
            asset["asset_id"]
            for asset in payload["assets"]
        }

    return known_assets


def _is_canonical_utc(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return False

    return (
        value.endswith("Z")
        and parsed.utcoffset() is not None
        and parsed.utcoffset().total_seconds() == 0
    )


def calculate_quality_gates(
    events: list[dict[str, Any]],
    known_assets: dict[str, set[str]],
) -> dict[str, Any]:
    """Calculate RW-050-2 quality gates for canonical events."""
    total = len(events)

    if total == 0:
        return {
            "passed": False,
            "status": "BLOCKED",
            "reason": "No canonical events available for validation.",
        }

    schema_valid_count = 0
    required_context_count = 0
    timestamp_success_count = 0
    known_asset_count = 0

    event_ids: list[str] = []
    duplicate_ids: set[str] = set()

    canonical_numeric_values = True
    canonical_utc_values = True

    for event in events:
        if not event.get("_validation_errors"):
            schema_valid_count += 1

        if REQUIRED_CONTEXT_FIELDS.issubset(event.keys()) and all(
            event.get(field) not in (None, "")
            for field in REQUIRED_CONTEXT_FIELDS
        ):
            required_context_count += 1

        timestamps_valid = all(
            _is_canonical_utc(event.get(field))
            for field in ("event_time", "ingest_time")
        )

        if timestamps_valid:
            timestamp_success_count += 1
        else:
            canonical_utc_values = False

        industry = event.get("industry")
        asset_id = event.get("asset_id")

        if (
            industry in known_assets
            and asset_id in known_assets[industry]
        ):
            known_asset_count += 1

        event_id = event.get("event_id")
        if isinstance(event_id, str):
            event_ids.append(event_id)

        metrics = event.get("metrics")
        if isinstance(metrics, dict):
            for value in metrics.values():
                if isinstance(value, bool) or not isinstance(
                    value, (int, float)
                ):
                    canonical_numeric_values = False
        else:
            canonical_numeric_values = False

    for event_id in event_ids:
        if event_ids.count(event_id) > 1:
            duplicate_ids.add(event_id)

    schema_validity = schema_valid_count / total
    required_context = required_context_count / total
    timestamp_parse_success = timestamp_success_count / total
    known_asset_resolution = known_asset_count / total

    gates = {
        "schema_validity": {
            "value": schema_validity,
            "threshold": QUALITY_THRESHOLDS["schema_validity"],
            "passed": schema_validity >= QUALITY_THRESHOLDS["schema_validity"],
        },
        "required_context": {
            "value": required_context,
            "threshold": QUALITY_THRESHOLDS["required_context"],
            "passed": required_context >= QUALITY_THRESHOLDS["required_context"],
        },
        "timestamp_parse_success": {
            "value": timestamp_parse_success,
            "threshold": QUALITY_THRESHOLDS["timestamp_parse_success"],
            "passed": timestamp_parse_success
            >= QUALITY_THRESHOLDS["timestamp_parse_success"],
        },
        "known_asset_resolution": {
            "value": known_asset_resolution,
            "threshold": QUALITY_THRESHOLDS["known_asset_resolution"],
            "passed": known_asset_resolution
            >= QUALITY_THRESHOLDS["known_asset_resolution"],
        },
        "duplicate_event_id": {
            "value": len(duplicate_ids),
            "threshold": QUALITY_THRESHOLDS["duplicate_event_id"],
            "passed": len(duplicate_ids) == 0,
        },
        "canonical_numeric_values": {
            "status": "PASS"
            if canonical_numeric_values
            else "FAIL",
            "passed": canonical_numeric_values,
        },
        "canonical_utc": {
            "status": "PASS"
            if canonical_utc_values
            else "FAIL",
            "passed": canonical_utc_values,
        },
        "canonical_units": {
            "status": "CONTRACT_ONLY",
            "passed": True,
            "note": (
                "Canonical units are required by the event contract, "
                "but no machine-readable unit registry exists in the "
                "current repository."
            ),
        },
    }

    return {
        "total_events": total,
        "gates": gates,
        "duplicate_event_ids": sorted(duplicate_ids),
        "passed": all(
            gate["passed"] for gate in gates.values()
        ),
        "status": (
            "PASS"
            if all(gate["passed"] for gate in gates.values())
            else "BLOCKED"
        ),
    }
