from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Iterable

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


def scenario_content_signature(
    events: Iterable[ObservableScenarioEvent],
) -> tuple[tuple[object, ...], ...]:
    """
    Build a deterministic content-only signature for one scenario.

    Scenario identifiers, seeds, split names and sequence indexes are excluded
    so that similarity is based on observable event content rather than the
    assignment metadata.
    """

    signature = []

    for event in events:
        signature.append(
            (
                event.event_family,
                event.event_type,
                event.asset_id,
                tuple(sorted(event.attributes.items())),
            )
        )

    return tuple(signature)


def sequence_similarity(
    left: tuple[tuple[object, ...], ...],
    right: tuple[tuple[object, ...], ...],
) -> float:
    """Return positional similarity between two observable sequences."""

    if not left and not right:
        return 1.0

    if not left or not right:
        return 0.0

    comparable = min(len(left), len(right))
    matches = sum(
        left[index] == right[index]
        for index in range(comparable)
    )

    length_penalty = abs(len(left) - len(right))

    return matches / max(len(left), len(right), length_penalty or 1)


def find_cross_split_near_duplicates(
    scenarios: dict[str, list[ObservableScenarioEvent]],
    similarity_threshold: float = 0.95,
) -> list[dict[str, object]]:
    """
    Find highly similar scenario sequences that belong to different splits.

    The comparison is deterministic and uses only observable scenario content.
    """

    signatures = {
        scenario_id: scenario_content_signature(events)
        for scenario_id, events in scenarios.items()
    }

    metadata = {
        scenario_id: {
            "scenario_id": scenario_id,
            "split": events[0].split if events else None,
        }
        for scenario_id, events in scenarios.items()
    }

    findings: list[dict[str, object]] = []
    scenario_ids = sorted(signatures)

    for index, left_id in enumerate(scenario_ids):
        for right_id in scenario_ids[index + 1 :]:
            left_split = metadata[left_id]["split"]
            right_split = metadata[right_id]["split"]

            if left_split == right_split:
                continue

            similarity = sequence_similarity(
                signatures[left_id],
                signatures[right_id],
            )

            if similarity >= similarity_threshold:
                findings.append(
                    {
                        "left_scenario_id": left_id,
                        "right_scenario_id": right_id,
                        "left_split": left_split,
                        "right_split": right_split,
                        "similarity": round(similarity, 6),
                    }
                )

    return findings
