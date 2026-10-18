"""Tests for the Cycle 3 shared observable evidence vocabulary."""

from dataclasses import FrozenInstanceError, replace

import pytest

from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    Cycle3EvidenceDefinition,
    SHARED_EVIDENCE_VOCABULARY,
    get_cycle3_evidence_definition,
    validate_cycle3_evidence_vocabulary,
)


def test_vocabulary_contains_twelve_definitions():
    assert len(SHARED_EVIDENCE_VOCABULARY) == 12


def test_all_entries_are_evidence_definitions():
    assert all(
        isinstance(item, Cycle3EvidenceDefinition)
        for item in SHARED_EVIDENCE_VOCABULARY
    )


def test_event_types_are_unique():
    names = [
        item.event_type
        for item in SHARED_EVIDENCE_VOCABULARY
    ]
    assert len(names) == len(set(names))


def test_event_types_are_nonempty():
    assert all(
        item.event_type
        for item in SHARED_EVIDENCE_VOCABULARY
    )


def test_evidence_domains_are_nonempty():
    assert all(
        item.evidence_domain
        for item in SHARED_EVIDENCE_VOCABULARY
    )


def test_descriptions_are_nonempty():
    assert all(
        item.description
        for item in SHARED_EVIDENCE_VOCABULARY
    )


def test_measurement_kinds_are_supported():
    allowed = {"count", "boolean", "duration"}

    assert all(
        item.measurement_kind in allowed
        for item in SHARED_EVIDENCE_VOCABULARY
    )


def test_boolean_measurements_have_no_unit():
    for item in SHARED_EVIDENCE_VOCABULARY:
        if item.measurement_kind == "boolean":
            assert item.unit is None


def test_numeric_measurements_have_units():
    for item in SHARED_EVIDENCE_VOCABULARY:
        if item.measurement_kind in {"count", "duration"}:
            assert item.unit


def test_count_measurements_have_expected_units():
    allowed = {"events", "sessions", "peers", "operations"}

    for item in SHARED_EVIDENCE_VOCABULARY:
        if item.measurement_kind == "count":
            assert item.unit in allowed


def test_duration_measurement_uses_seconds():
    definitions = [
        item
        for item in SHARED_EVIDENCE_VOCABULARY
        if item.measurement_kind == "duration"
    ]

    assert definitions
    assert all(item.unit == "seconds" for item in definitions)


def test_lookup_existing_event_type():
    result = get_cycle3_evidence_definition(
        "file_write_activity"
    )

    assert result.event_type == "file_write_activity"
    assert result.evidence_domain == "file"
    assert result.measurement_kind == "count"
    assert result.unit == "operations"


def test_lookup_unknown_event_type_rejected():
    with pytest.raises(KeyError, match="Unknown Cycle 3"):
        get_cycle3_evidence_definition(
            "nonexistent_event_type"
        )


@pytest.mark.parametrize(
    "event_type",
    [
        "authentication_activity",
        "file_write_activity",
        "file_rename_activity",
        "service_state_observation",
        "backup_status_observation",
        "telemetry_freshness_observation",
        "maintenance_authorization_observation",
    ],
)
def test_lookup_returns_correct_definition(event_type):
    result = get_cycle3_evidence_definition(event_type)
    assert result.event_type == event_type


def test_vocabulary_validation_passes():
    assert validate_cycle3_evidence_vocabulary() is None


def test_definition_is_immutable():
    definition = SHARED_EVIDENCE_VOCABULARY[0]

    with pytest.raises(FrozenInstanceError):
        definition.event_type = "modified"


def test_vocabulary_container_is_tuple():
    assert isinstance(SHARED_EVIDENCE_VOCABULARY, tuple)


def test_no_scenario_labels_in_event_names():
    forbidden = ("attack", "benign", "fault", "normal")

    for item in SHARED_EVIDENCE_VOCABULARY:
        assert not any(
            label in item.event_type
            for label in forbidden
        )


def test_all_definitions_can_be_resolved():
    for item in SHARED_EVIDENCE_VOCABULARY:
        assert get_cycle3_evidence_definition(
            item.event_type
        ) == item


def test_lookup_is_deterministic():
    first = get_cycle3_evidence_definition(
        "network_peer_activity"
    )

    second = get_cycle3_evidence_definition(
        "network_peer_activity"
    )

    assert first == second


def test_replacement_does_not_mutate_original():
    original = SHARED_EVIDENCE_VOCABULARY[0]

    modified = replace(
        original,
        description="Modified test description",
    )

    assert original.description != modified.description
    assert modified.event_type == original.event_type


def test_vocabulary_has_multiple_evidence_domains():
    domains = {
        item.evidence_domain
        for item in SHARED_EVIDENCE_VOCABULARY
    }

    assert len(domains) >= 5


def test_shared_vocabulary_excludes_historical_template_names():
    forbidden = {
        "initial_access_observable",
        "execution_persistence_observable",
        "patching",
        "host_outage",
        "identity_baseline",
    }

    names = {
        item.event_type
        for item in SHARED_EVIDENCE_VOCABULARY
    }

    assert names.isdisjoint(forbidden)
