"""Cycle 3 measurement-quality gate.

Development-only diagnostic. Does not train models, modify
historical feature contracts, or change runtime decisions.
"""

from dataclasses import dataclass

from config.ransomware.scenarios.cycle3_measurement_audit import (
    Cycle3MeasurementAudit,
)


@dataclass(frozen=True)
class Cycle3MeasurementQualityResult:
    passed: bool
    missing_fraction: float
    reasons: tuple[str, ...]


def evaluate_cycle3_measurement_quality(
    audit: Cycle3MeasurementAudit,
    *,
    max_missing_fraction: float = 0.0,
    allow_mixed_sources: bool = False,
) -> Cycle3MeasurementQualityResult:
    """Evaluate explicit numerical-provenance quality constraints."""

    if not 0.0 <= max_missing_fraction <= 1.0:
        raise ValueError(
            "max_missing_fraction must be between 0 and 1"
        )

    reasons = []

    if audit.event_count == 0:
        reasons.append("empty_event_window")
        missing_fraction = 1.0
    else:
        missing_fraction = (
            audit.missing_event_count / audit.event_count
        )

    if audit.nonfinite_value_count:
        reasons.append("nonfinite_numerical_values")

    if missing_fraction > max_missing_fraction:
        reasons.append("missing_numerical_values")

    if audit.mixed_sources and not allow_mixed_sources:
        reasons.append("mixed_numerical_sources")

    return Cycle3MeasurementQualityResult(
        passed=not reasons,
        missing_fraction=missing_fraction,
        reasons=tuple(reasons),
    )
