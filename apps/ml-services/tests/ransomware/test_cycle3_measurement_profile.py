"""Tests for the shared Cycle 3 synthetic measurement profile."""

from dataclasses import fields, replace

import pytest

from config.ransomware.scenarios.cycle3_measurement_profile import (
    OBSERVATION_MINUTES,
    PROFILE_VERSION,
    REQUIRED_EVENT_TYPES,
    build_cycle3_measurement_profile,
    validate_cycle3_measurement_profile,
)


EXPECTED_KINDS = (
    ("privilege_change_activity", "boolean"),
    ("file_write_activity", "count"),
    ("file_rename_activity", "count"),
    ("service_state_observation", "boolean"),
    ("telemetry_freshness_observation", "duration"),
)


def test_profile_builds_successfully():
    profile = build_cycle3_measurement_profile()

    validate_cycle3_measurement_profile(profile)


def test_profile_version():
    profile = build_cycle3_measurement_profile()

    assert profile.version == PROFILE_VERSION


def test_profile_contains_exactly_five_evidence_types():
    profile = build_cycle3_measurement_profile()

    assert profile.event_types == REQUIRED_EVENT_TYPES
    assert len(profile.event_types) == 5
    assert len(set(profile.event_types)) == 5


def test_profile_observation_schedule():
    profile = build_cycle3_measurement_profile()

    assert profile.observation_minutes == tuple(range(1, 16))
    assert profile.observation_minutes == OBSERVATION_MINUTES


def test_profile_measurement_kinds():
    profile = build_cycle3_measurement_profile()

    assert profile.measurement_kinds == EXPECTED_KINDS


def test_profile_contains_no_label_or_lifecycle_fields():
    profile = build_cycle3_measurement_profile()

    names = {item.name for item in fields(profile)}

    forbidden = {
        "variant",
        "label",
        "attack_label",
        "scenario_family",
        "lifecycle_stage",
        "stage",
        "is_attack",
        "target",
    }

    assert names.isdisjoint(forbidden)


def test_profile_is_immutable():
    profile = build_cycle3_measurement_profile()

    with pytest.raises(AttributeError):
        profile.version = "modified"


@pytest.mark.parametrize(
    "invalid_version",
    (
        "",
        "cycle3_measurement_profile_v0",
        "cycle3_measurement_profile_v2",
    ),
)
def test_rejects_invalid_version(invalid_version):
    profile = build_cycle3_measurement_profile()

    with pytest.raises(ValueError):
        validate_cycle3_measurement_profile(
            replace(profile, version=invalid_version)
        )


@pytest.mark.parametrize(
    "invalid_schedule",
    (
        (),
        (1, 2, 3),
        tuple(range(0, 15)),
        tuple(range(2, 17)),
        tuple(range(1, 16)) + (15,),
        tuple(reversed(range(1, 16))),
        (True,) + tuple(range(2, 16)),
    ),
)
def test_rejects_invalid_schedule(invalid_schedule):
    profile = build_cycle3_measurement_profile()

    with pytest.raises(ValueError):
        validate_cycle3_measurement_profile(
            replace(
                profile,
                observation_minutes=invalid_schedule,
            )
        )


@pytest.mark.parametrize(
    "invalid_event_types",
    (
        (),
        ("unknown_event_type",),
        ("maintenance_authorization_observation",),
        REQUIRED_EVENT_TYPES[:-1],
        REQUIRED_EVENT_TYPES + ("file_write_activity",),
        tuple(reversed(REQUIRED_EVENT_TYPES)),
    ),
)
def test_rejects_invalid_evidence_types(invalid_event_types):
    profile = build_cycle3_measurement_profile()

    with pytest.raises(ValueError):
        validate_cycle3_measurement_profile(
            replace(
                profile,
                event_types=invalid_event_types,
            )
        )


@pytest.mark.parametrize(
    "invalid_kinds",
    (
        (),
        EXPECTED_KINDS[:-1],
        EXPECTED_KINDS + (
            ("unknown_event_type", "count"),
        ),
        (
            ("privilege_change_activity", "count"),
        ) + EXPECTED_KINDS[1:],
        tuple(reversed(EXPECTED_KINDS)),
    ),
)
def test_rejects_invalid_measurement_kinds(invalid_kinds):
    profile = build_cycle3_measurement_profile()

    with pytest.raises(ValueError):
        validate_cycle3_measurement_profile(
            replace(
                profile,
                measurement_kinds=invalid_kinds,
            )
        )


def test_rejects_non_profile_object():
    with pytest.raises(ValueError):
        validate_cycle3_measurement_profile(
            {"version": PROFILE_VERSION}
        )


def test_repeated_builds_are_deterministic():
    first = build_cycle3_measurement_profile()
    second = build_cycle3_measurement_profile()

    assert first == second


def test_profile_has_no_variant_specific_configuration():
    profile = build_cycle3_measurement_profile()

    representation = repr(profile).lower()

    for forbidden in (
        "ransomware",
        "encryption_impact",
        "lateral_movement",
        "scenario_family",
        "attack_label",
    ):
        assert forbidden not in representation
