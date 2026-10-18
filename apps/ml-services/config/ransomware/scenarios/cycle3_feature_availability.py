"""Cycle 3 feature-specific measurement availability contract."""

from dataclasses import dataclass
from typing import Iterable

from config.ransomware.scenarios.cycle3_evidence_feature_contract import (
    EVIDENCE_FEATURE_MAPPINGS,
)
from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    evaluate_cycle3_measurement_value,
)
from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    evaluate_cycle3_evidence_mapping,
)


@dataclass(frozen=True)
class Cycle3FeatureAvailability:
    event_type: str
    feature_name: str
    status: str
    observed_count: int
    valid_count: int
    invalid_count: int


def audit_cycle3_feature_availability(
    events: Iterable,
) -> tuple[Cycle3FeatureAvailability, ...]:
    """Audit measurement presence without inventing feature values."""

    window = tuple(events)
    results = []

    compatible = [
        mapping
        for mapping in EVIDENCE_FEATURE_MAPPINGS
        if mapping.status == "compatible_with_constraints"
    ]

    for mapping in compatible:
        relevant = [
            event
            for event in window
            if event.event_type == mapping.event_type
        ]

        valid_count = 0
        invalid_count = 0

        for event in relevant:
            value = event.attributes.get(
                mapping.attribute_name
            )

            decision = evaluate_cycle3_measurement_value(
                mapping.event_type,
                value,
            )

            if decision.allowed:
                valid_count += 1
            else:
                invalid_count += 1

        if invalid_count:
            status = "invalid"
        elif valid_count:
            status = "available"
        else:
            status = "missing"

        results.append(
            Cycle3FeatureAvailability(
                event_type=mapping.event_type,
                feature_name=mapping.feature_name,
                status=status,
                observed_count=len(relevant),
                valid_count=valid_count,
                invalid_count=invalid_count,
            )
        )

    return tuple(results)



@dataclass(frozen=True)
class Cycle3QuarantinedEvidence:
    event_type: str
    reason: str
    observed_count: int


def audit_cycle3_quarantined_evidence(
    events: Iterable,
) -> tuple[Cycle3QuarantinedEvidence, ...]:
    """Report rejected evidence types without converting them to features."""

    rejected_counts: dict[tuple[str, str], int] = {}

    for event in events:
        decision = evaluate_cycle3_evidence_mapping(
            event.event_type
        )

        if decision.allowed:
            continue

        reason = decision.reason

        if reason is None:
            raise ValueError(
                "Rejected evidence must include a reason."
            )

        key = (event.event_type, reason)

        rejected_counts[key] = (
            rejected_counts.get(key, 0) + 1
        )

    return tuple(
        Cycle3QuarantinedEvidence(
            event_type=event_type,
            reason=reason,
            observed_count=count,
        )
        for (event_type, reason), count in sorted(
            rejected_counts.items()
        )
    )
