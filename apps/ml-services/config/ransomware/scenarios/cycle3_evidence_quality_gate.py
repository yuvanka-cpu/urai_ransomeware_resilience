"""Fail-closed Cycle 3 evidence-quality admission contract."""

from dataclasses import dataclass
from typing import Iterable

from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    evaluate_cycle3_evidence_mapping,
)
from config.ransomware.scenarios.cycle3_feature_availability import (
    Cycle3FeatureAvailability,
    Cycle3QuarantinedEvidence,
    audit_cycle3_feature_availability,
    audit_cycle3_quarantined_evidence,
)


@dataclass(frozen=True)
class Cycle3EvidenceQualityDecision:
    passed: bool
    reasons: tuple[str, ...]
    required_event_types: tuple[str, ...]
    availability: tuple[Cycle3FeatureAvailability, ...]
    quarantined: tuple[Cycle3QuarantinedEvidence, ...]


def evaluate_cycle3_evidence_quality(
    events: Iterable,
    *,
    required_event_types: Iterable[str],
) -> Cycle3EvidenceQualityDecision:
    """Admit evidence only when explicit requirements are satisfied."""

    window = tuple(events)
    required = tuple(required_event_types)

    if not required:
        raise ValueError(
            "required_event_types must not be empty"
        )

    if any(
        not isinstance(event_type, str) or not event_type
        for event_type in required
    ):
        raise ValueError(
            "required_event_types must contain nonempty strings"
        )

    if len(required) != len(set(required)):
        raise ValueError(
            "required_event_types must not contain duplicates"
        )

    reasons = []

    for event_type in required:
        decision = evaluate_cycle3_evidence_mapping(event_type)

        if not decision.allowed:
            reasons.append(
                f"invalid_required_evidence:{event_type}:"
                f"{decision.reason}"
            )

    availability = audit_cycle3_feature_availability(window)
    quarantined = audit_cycle3_quarantined_evidence(window)

    if not window:
        reasons.append("empty_event_window")

    for item in quarantined:
        reasons.append(
            f"quarantined_evidence:{item.event_type}:{item.reason}"
        )

    availability_by_type = {
        item.event_type: item
        for item in availability
    }

    for event_type in required:
        item = availability_by_type.get(event_type)

        if item is None:
            continue

        if item.status != "available":
            reasons.append(
                f"required_evidence_{item.status}:{event_type}"
            )

    return Cycle3EvidenceQualityDecision(
        passed=not reasons,
        reasons=tuple(reasons),
        required_event_types=required,
        availability=availability,
        quarantined=quarantined,
    )
