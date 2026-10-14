"""RW-130-3: Offline incident timing metrics.

Requires independently supplied incident timestamps.
Does not infer timestamps from model timesteps or execute response actions.
"""

from datetime import datetime, timezone
from math import isfinite


TIMESTAMP_FIELDS = (
    "incident_onset_at",
    "detected_at",
    "response_started_at",
    "recovery_completed_at",
)

METRIC_FIELDS = {
    "mttd": ("incident_onset_at", "detected_at"),
    "mean_response_time": ("detected_at", "response_started_at"),
    "mean_recovery_time": ("incident_onset_at", "recovery_completed_at"),
}


def _parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def calculate_incident_timing(incidents):
    """Calculate mean elapsed minutes for complete, valid incident records.

    Missing timestamps exclude an incident from the relevant metric.
    Invalid timestamps, reversed event order, and duplicate IDs fail closed.
    """
    unavailable = lambda reason: {
        "status": "unavailable",
        "reason": reason,
        "metrics": {},
    }

    if not isinstance(incidents, list) or not incidents:
        return unavailable("A nonempty list of incidents is required.")

    seen_ids = set()
    parsed_incidents = []

    for incident in incidents:
        if not isinstance(incident, dict):
            return unavailable("Each incident must be a dictionary.")

        incident_id = incident.get("incident_id")
        if not isinstance(incident_id, str) or not incident_id.strip():
            return unavailable("Each incident requires a valid incident_id.")
        if incident_id in seen_ids:
            return unavailable("Duplicate incident_id.")
        seen_ids.add(incident_id)

        parsed = {
            field: _parse_timestamp(incident.get(field))
            for field in TIMESTAMP_FIELDS
        }

        for field in TIMESTAMP_FIELDS:
            supplied = incident.get(field)
            if supplied is not None and parsed[field] is None:
                return unavailable(f"Invalid {field} for {incident_id}.")

        present = [
            parsed[field] for field in TIMESTAMP_FIELDS
            if parsed[field] is not None
        ]
        if present != sorted(present):
            return unavailable(f"Invalid event chronology for {incident_id}.")

        parsed_incidents.append(parsed)

    metrics = {}

    for name, (start_field, end_field) in METRIC_FIELDS.items():
        durations = []

        for incident in parsed_incidents:
            start = incident[start_field]
            end = incident[end_field]
            if start is not None and end is not None:
                minutes = (end - start).total_seconds() / 60
                if not isfinite(minutes) or minutes < 0:
                    return unavailable("Invalid incident duration.")
                durations.append(minutes)

        metrics[name] = {
            "status": "available" if durations else "unavailable",
            "mean_minutes": (
                sum(durations) / len(durations) if durations else None
            ),
            "sample_count": len(durations),
            "excluded_count": len(parsed_incidents) - len(durations),
        }

    return {
        "status": (
            "available"
            if all(metric["status"] == "available" for metric in metrics.values())
            else "partial"
            if any(metric["status"] == "available" for metric in metrics.values())
            else "unavailable"
        ),
        "reason": None,
        "incident_count": len(parsed_incidents),
        "metrics": metrics,
        "scope": "offline_incident_timing",
        "data_source": "supplied_incident_records",
    }
