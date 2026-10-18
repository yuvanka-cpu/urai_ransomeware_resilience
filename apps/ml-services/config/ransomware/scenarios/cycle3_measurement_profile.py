"""Cycle 3 synthetic measurement profile.

This module defines the shared observation contract for a future
synthetic measurement generator.

It does not generate measurements, assign labels, or train models.

The same evidence vocabulary and schedule apply to every scenario
variant. Measurement realism and statistical leakage must be audited
separately before any model-training use.
"""

from dataclasses import dataclass

from config.ransomware.scenarios.cycle3_evidence_feature_contract import (
    get_cycle3_evidence_feature_mapping,
)
from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    evaluate_cycle3_evidence_mapping,
)
from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    get_cycle3_evidence_definition,
)


@dataclass(frozen=True)
class Cycle3MeasurementProfile:
    """Shared, variant-independent synthetic observation contract."""

    version: str
    event_types: tuple[str, ...]
    observation_minutes: tuple[int, ...]
    measurement_kinds: tuple[tuple[str, str], ...]


PROFILE_VERSION = "cycle3_measurement_profile_v1"

REQUIRED_EVENT_TYPES = (
    "privilege_change_activity",
    "file_write_activity",
    "file_rename_activity",
    "service_state_observation",
    "telemetry_freshness_observation",
)

OBSERVATION_MINUTES = tuple(range(1, 16))


def validate_cycle3_measurement_profile(
    profile: Cycle3MeasurementProfile,
) -> None:
    """Reject incomplete or incompatible measurement profiles."""

    if not isinstance(profile, Cycle3MeasurementProfile):
        raise ValueError("Invalid measurement profile")

    if profile.version != PROFILE_VERSION:
        raise ValueError("Unsupported measurement profile version")

    if profile.event_types != REQUIRED_EVENT_TYPES:
        raise ValueError("Unexpected measurement evidence types")

    if len(profile.event_types) != len(set(profile.event_types)):
        raise ValueError("Duplicate measurement evidence types")

    if profile.observation_minutes != OBSERVATION_MINUTES:
        raise ValueError("Unexpected observation schedule")

    if any(
        type(minute) is not int or minute <= 0
        for minute in profile.observation_minutes
    ):
        raise ValueError("Invalid observation minute")

    expected_kinds = []

    for event_type in profile.event_types:
        decision = evaluate_cycle3_evidence_mapping(event_type)

        if not decision.allowed:
            raise ValueError(
                f"Unresolved measurement mapping: {event_type}"
            )

        mapping = get_cycle3_evidence_feature_mapping(event_type)

        if (
            mapping.attribute_name is None
            or mapping.feature_name is None
        ):
            raise ValueError(
                f"Incomplete measurement mapping: {event_type}"
            )

        definition = get_cycle3_evidence_definition(event_type)

        expected_kinds.append(
            (event_type, definition.measurement_kind)
        )

    if profile.measurement_kinds != tuple(expected_kinds):
        raise ValueError("Measurement kind contract mismatch")


def build_cycle3_measurement_profile() -> Cycle3MeasurementProfile:
    """Construct and validate the shared Cycle 3 measurement profile."""

    measurement_kinds = tuple(
        (
            event_type,
            get_cycle3_evidence_definition(
                event_type
            ).measurement_kind,
        )
        for event_type in REQUIRED_EVENT_TYPES
    )

    profile = Cycle3MeasurementProfile(
        version=PROFILE_VERSION,
        event_types=REQUIRED_EVENT_TYPES,
        observation_minutes=OBSERVATION_MINUTES,
        measurement_kinds=measurement_kinds,
    )

    validate_cycle3_measurement_profile(profile)

    return profile
