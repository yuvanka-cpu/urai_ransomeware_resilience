"""Read-only, development-only synthetic observable timeline gateway."""

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app.policies.ransomware_policy import validate_synthetic_request
from app.schemas.requests import RansomwareRequest
from app.services.ransomware_timeline_validation import valid_timeline_evidence
from app.services.ransomware_ml_gateway import ML_SERVICE_URL


router = APIRouter()

TIMELINE_ENDPOINT = (
    f"{ML_SERVICE_URL}/internal/ransomware/observable-timeline"
)


def unavailable(reason: str) -> dict[str, Any]:
    return {
        "task_id": "RW-120-6",
        "status": "unavailable",
        "data_provenance": "synthetic_development",
        "is_operational_incident_timeline": False,
        "timeline": [],
        "reason": reason,
    }



def valid_timeline_events(events: list[dict[str, Any]]) -> bool:
    """Validate ordered synthetic observable events before displaying them."""
    previous_time = None

    for expected_index, event in enumerate(events):
        if not isinstance(event, dict):
            return False

        index = event.get("sequence_index")
        if type(index) is not int or index != expected_index:
            return False

        timestamp = event.get("event_time")
        if not isinstance(timestamp, str):
            return False

        try:
            parsed_time = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
        except ValueError:
            return False

        if parsed_time.tzinfo is None:
            return False

        parsed_time = parsed_time.astimezone(timezone.utc)

        if previous_time is not None and parsed_time < previous_time:
            return False

        previous_time = parsed_time

        for field in ("event_family", "event_type", "asset_id"):
            value = event.get(field)
            if not isinstance(value, str) or not value.strip():
                return False

        attributes = event.get("attributes")
        if not isinstance(attributes, dict):
            return False

    return True


@router.post("/api/v1/ransomware/observable-timeline")
def get_observable_timeline(request: RansomwareRequest) -> dict[str, Any]:
    """Retrieve validated synthetic events without executing inference."""
    try:
        validate_synthetic_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = {
        "schema_version": request.schema_version,
        "mode": "synthetic_scenario",
        "industry": request.industry.value,
        "site_id": request.site_id,
        "site_type": request.site_type.value,
        "scenario_id": request.scenario_id,
        "observable_input": request.observable_input,
    }

    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.post(TIMELINE_ENDPOINT, json=payload)
    except (httpx.RequestError, httpx.TimeoutException):
        return unavailable("Synthetic timeline dependency is unavailable.")

    if response.status_code != 200:
        return unavailable(
            "No permitted development-only timeline evidence is available."
        )

    try:
        body = response.json()
    except ValueError:
        return unavailable("Synthetic timeline dependency returned invalid JSON.")

    if not isinstance(body, dict):
        return unavailable("Synthetic timeline response is not an object.")

    if (
        body.get("task_id") != "RW-120-6"
        or body.get("schema_version") != "1.0"
        or body.get("scenario_id") != request.scenario_id
        or body.get("data_provenance") != "synthetic_development"
        or body.get("is_operational_incident_timeline") is not False
        or body.get("status") not in {"available", "unavailable"}
    ):
        return unavailable("Synthetic timeline response contract is invalid.")

    if body["status"] == "unavailable":
        return unavailable(
            "Synthetic observable timeline evidence failed validation."
        )

    timeline = body.get("timeline")
    event_count = body.get("event_count")

    if (
        not isinstance(timeline, list)
        or not isinstance(event_count, int)
        or isinstance(event_count, bool)
        or event_count <= 0
        or len(timeline) != event_count
        or not valid_timeline_evidence(body)
    ):
        return unavailable("Synthetic timeline event structure is invalid.")

    return body
