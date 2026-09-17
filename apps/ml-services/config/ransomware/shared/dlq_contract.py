from enum import Enum
from typing import Any


class DLQReason(str, Enum):
    REQUIRED_FIELD_MISSING = "required_field_missing"
    INVALID_ENCODING = "invalid_encoding"
    INVALID_UNIT = "invalid_unit"
    INCOMPATIBLE_STRUCTURE = "incompatible_structure"
    NORMALIZATION_FAILURE = "normalization_failure"


class DLQEnvelope:
    """Metadata-only envelope for source records rejected during normalization."""

    def __init__(
        self,
        event_id: str,
        source_system: str,
        reason_code: DLQReason,
        message: str,
        raw_payload: Any,
    ):
        self.event_id = event_id
        self.source_system = source_system
        self.reason_code = reason_code
        self.message = message
        self.raw_payload = raw_payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source_system": self.source_system,
            "reason_code": self.reason_code.value,
            "message": self.message,
            "raw_payload": self.raw_payload,
        }

def create_dlq_envelope(
    event_id: str,
    source_system: str,
    reason_code: DLQReason,
    message: str,
    raw_payload: Any,
) -> DLQEnvelope:
    """Create a deterministic DLQ envelope for a rejected source record."""
    if not isinstance(reason_code, DLQReason):
        raise ValueError("invalid DLQ reason code")

    return DLQEnvelope(
        event_id=event_id,
        source_system=source_system,
        reason_code=reason_code,
        message=message,
        raw_payload=raw_payload,
    )
