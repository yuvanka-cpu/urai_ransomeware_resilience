"""Safe, non-executing canonical event validation and DLQ routing."""

from __future__ import annotations

import json
from typing import Any

from config.ransomware.shared.dlq_contract import (
    DLQEnvelope,
    DLQReason,
    create_dlq_envelope,
)
from config.ransomware.shared.validation.canonical_event_validator import (
    validate_event,
)


def route_canonical_event(
    event: Any,
) -> tuple[dict[str, Any] | None, DLQEnvelope | None]:
    """Return either a validated event or a DLQ envelope.

    This function does not publish messages, execute operational
    actions, modify the input or silently coerce invalid values.
    """

    if not isinstance(event, dict):
        errors = ["canonical event must be a JSON object"]
        reason = DLQReason.INCOMPATIBLE_STRUCTURE
    else:
        errors = validate_event(event)

        if not errors:
            return event, None

        if any(
            error.startswith("missing required field:")
            for error in errors
        ):
            reason = DLQReason.REQUIRED_FIELD_MISSING
        else:
            reason = DLQReason.INCOMPATIBLE_STRUCTURE

    event_id = (
        event.get("event_id")
        if isinstance(event, dict)
        else None
    )
    source_system = (
        event.get("source_system")
        if isinstance(event, dict)
        else None
    )

    raw_payload = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    envelope = create_dlq_envelope(
        event_id=event_id if isinstance(event_id, str) else "",
        source_system=(
            source_system
            if isinstance(source_system, str)
            else ""
        ),
        reason_code=reason,
        message="; ".join(errors),
        raw_payload=raw_payload,
    )

    return None, envelope
