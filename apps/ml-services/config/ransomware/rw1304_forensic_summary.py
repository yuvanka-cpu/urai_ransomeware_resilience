"""RW-130-4: Offline synthetic forensic evidence summary.

Uses observable synthetic events only. Does not establish compromise,
attacker identity, causality, or operational incident timelines.
"""

from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from math import isfinite

from config.ransomware.scenarios.scenario_event_assembler import (
    sequence_fingerprint,
)


REQUIRED_FIELDS = (
    "scenario_id",
    "sequence_index",
    "event_time",
    "event_family",
    "event_type",
    "asset_id",
    "attributes",
)

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


def _contains_truth(value):
    if isinstance(value, dict):
        return any(
            str(key).strip().lower() in FORBIDDEN_KEYS
            or _contains_truth(child)
            for key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_truth(item) for item in value)
    return False


def _valid_attributes(value):
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, (list, tuple)):
        return all(_valid_attributes(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _valid_attributes(item)
            for key, item in value.items()
        )
    return False


def _parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def summarize_forensic_events(events):
    """Summarize validated observable events without asserting compromise."""
    def unavailable(reason):
        return {
            "status": "unavailable",
            "reason": reason,
            "scope": "offline_synthetic_observable_evidence",
        }

    if not isinstance(events, list) or not events:
        return unavailable("A nonempty event list is required.")

    validated = []
    scenario_ids = set()
    indexes = set()

    for event in events:
        if not is_dataclass(event) or isinstance(event, type):
            return unavailable("Expected ObservableScenarioEvent records.")

        record = asdict(event)

        if any(field not in record for field in REQUIRED_FIELDS):
            return unavailable("Missing required event fields.")

        if _contains_truth(record):
            return unavailable("Truth-bearing fields are forbidden.")

        for field in ("scenario_id", "event_family", "event_type", "asset_id"):
            if not isinstance(record[field], str) or not record[field].strip():
                return unavailable(f"Invalid {field}.")

        index = record["sequence_index"]
        if type(index) is not int or index < 0 or index in indexes:
            return unavailable("Invalid or duplicate sequence index.")

        if not isinstance(record["attributes"], dict):
            return unavailable("Event attributes must be a dictionary.")

        if not _valid_attributes(record["attributes"]):
            return unavailable("Unsupported or nonfinite event attributes.")

        timestamp = _parse_time(record["event_time"])
        if timestamp is None:
            return unavailable("Invalid event timestamp.")

        indexes.add(index)
        scenario_ids.add(record["scenario_id"])
        validated.append((index, timestamp, event, record))

    if len(scenario_ids) != 1:
        return unavailable("Events must belong to one scenario.")

    validated.sort(key=lambda item: item[0])

    timestamps = [item[1] for item in validated]
    if timestamps != sorted(timestamps):
        return unavailable("Event timestamps contradict sequence order.")

    ordered_events = [item[2] for item in validated]
    timeline = [
        {
            "sequence_index": record["sequence_index"],
            "event_time": record["event_time"],
            "event_family": record["event_family"],
            "event_type": record["event_type"],
            "asset_id": record["asset_id"],
            "attributes": record["attributes"],
        }
        for _, _, _, record in validated
    ]

    return {
        "status": "available",
        "scope": "offline_synthetic_observable_evidence",
        "scenario_id": next(iter(scenario_ids)),
        "event_count": len(timeline),
        "first_event_at": timeline[0]["event_time"],
        "last_event_at": timeline[-1]["event_time"],
        "observed_asset_ids": sorted({
            item["asset_id"] for item in timeline
        }),
        "event_family_counts": dict(sorted(Counter(
            item["event_family"] for item in timeline
        ).items())),
        "timeline": timeline,
        "sequence_fingerprint_sha256": sequence_fingerprint(ordered_events),
        "fingerprint_scope": (
            "Event sequence index, family, type, asset ID and attributes; "
            "timestamps are excluded."
        ),
        "limitations": (
            "Synthetic observable events only. Observed assets are not "
            "confirmed compromised assets. This is not a verified "
            "incident reconstruction or chain-of-custody record."
        ),
    }
