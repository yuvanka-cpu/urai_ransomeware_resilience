"""Fail-closed evidence-to-feature mapping gate for Cycle 3.

Development-only compatibility enforcement.

This module does not generate measurements, train models,
modify historical datasets, or execute industrial actions.
"""

from dataclasses import dataclass

from config.ransomware.scenarios.cycle3_evidence_feature_contract import (
    Cycle3EvidenceFeatureMapping,
    get_cycle3_evidence_feature_mapping,
)


@dataclass(frozen=True)
class Cycle3EvidenceMappingDecision:
    allowed: bool
    event_type: str
    mapping: Cycle3EvidenceFeatureMapping | None
    reason: str | None


def evaluate_cycle3_evidence_mapping(
    event_type: str,
) -> Cycle3EvidenceMappingDecision:
    """Evaluate whether an evidence type has a usable mapping."""

    try:
        mapping = get_cycle3_evidence_feature_mapping(event_type)
    except KeyError:
        return Cycle3EvidenceMappingDecision(
            allowed=False,
            event_type=event_type,
            mapping=None,
            reason="unknown_evidence_type",
        )

    if mapping.status != "compatible_with_constraints":
        return Cycle3EvidenceMappingDecision(
            allowed=False,
            event_type=event_type,
            mapping=None,
            reason="unresolved_measurement_semantics",
        )

    if not mapping.attribute_name or not mapping.feature_name:
        return Cycle3EvidenceMappingDecision(
            allowed=False,
            event_type=event_type,
            mapping=None,
            reason="incomplete_feature_mapping",
        )

    return Cycle3EvidenceMappingDecision(
        allowed=True,
        event_type=event_type,
        mapping=mapping,
        reason=None,
    )


def require_cycle3_evidence_mapping(
    event_type: str,
) -> Cycle3EvidenceFeatureMapping:
    """Return a compatible mapping or reject the evidence type."""

    decision = evaluate_cycle3_evidence_mapping(event_type)

    if not decision.allowed or decision.mapping is None:
        raise ValueError(
            f"Cycle 3 evidence mapping rejected: "
            f"{event_type!r} ({decision.reason})"
        )

    return decision.mapping
