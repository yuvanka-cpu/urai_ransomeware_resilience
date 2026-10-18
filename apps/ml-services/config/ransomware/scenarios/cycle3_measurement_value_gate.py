"""Fail-closed measurement-value validation for Cycle 3.

Development-only validation. Does not generate synthetic telemetry,
modify historical artifacts, train models, or execute industrial actions.
"""

from dataclasses import dataclass
from math import isfinite

from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    get_cycle3_evidence_definition,
)
from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    evaluate_cycle3_evidence_mapping,
)


@dataclass(frozen=True)
class Cycle3MeasurementValueDecision:
    allowed: bool
    event_type: str
    value: int | float | bool | None
    reason: str | None


def evaluate_cycle3_measurement_value(
    event_type: str,
    value: object,
) -> Cycle3MeasurementValueDecision:
    """Validate one measured value against its evidence definition."""

    mapping = evaluate_cycle3_evidence_mapping(event_type)

    if not mapping.allowed:
        return Cycle3MeasurementValueDecision(
            allowed=False,
            event_type=event_type,
            value=None,
            reason=mapping.reason,
        )

    definition = get_cycle3_evidence_definition(event_type)

    if value is None:
        reason = "missing_measurement"

    elif definition.measurement_kind == "boolean":
        reason = None if type(value) is bool else "invalid_boolean"

    elif definition.measurement_kind == "count":
        reason = (
            None
            if type(value) is int and value >= 0
            else "invalid_count"
        )

    elif definition.measurement_kind == "duration":
        if type(value) not in (int, float):
            reason = "invalid_duration"
        elif not isfinite(value):
            reason = "nonfinite_duration"
        elif value < 0:
            reason = "negative_duration"
        else:
            reason = None

    else:
        reason = "unsupported_measurement_kind"

    if reason is not None:
        return Cycle3MeasurementValueDecision(
            allowed=False,
            event_type=event_type,
            value=None,
            reason=reason,
        )

    return Cycle3MeasurementValueDecision(
        allowed=True,
        event_type=event_type,
        value=value,
        reason=None,
    )


def require_cycle3_measurement_value(
    event_type: str,
    value: object,
) -> int | float | bool:
    """Return a valid measurement or raise without substituting defaults."""

    decision = evaluate_cycle3_measurement_value(
        event_type,
        value,
    )

    if not decision.allowed or decision.value is None:
        raise ValueError(
            "Cycle 3 measurement rejected: "
            f"{event_type!r} ({decision.reason})"
        )

    return decision.value
