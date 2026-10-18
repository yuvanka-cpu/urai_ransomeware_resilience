"""Tests for Cycle 3 shared evidence-to-feature compatibility."""

from dataclasses import FrozenInstanceError, replace

import pytest

from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    SHARED_EVIDENCE_VOCABULARY,
)

from config.ransomware.scenarios.cycle3_evidence_feature_contract import (
    Cycle3EvidenceFeatureMapping,
    EVIDENCE_FEATURE_MAPPINGS,
    get_cycle3_evidence_feature_mapping,
    validate_cycle3_evidence_feature_mappings,
)


def test_mapping_count_matches_vocabulary():
    assert len(EVIDENCE_FEATURE_MAPPINGS) == len(
        SHARED_EVIDENCE_VOCABULARY
    )


def test_exactly_twelve_mappings():
    assert len(EVIDENCE_FEATURE_MAPPINGS) == 12


def test_all_entries_have_expected_type():
    assert all(
        isinstance(mapping, Cycle3EvidenceFeatureMapping)
        for mapping in EVIDENCE_FEATURE_MAPPINGS
    )


def test_mapping_event_types_are_unique():
    names = [mapping.event_type for mapping in EVIDENCE_FEATURE_MAPPINGS]
    assert len(names) == len(set(names))


def test_mapping_coverage_matches_vocabulary():
    vocabulary = {
        definition.event_type
        for definition in SHARED_EVIDENCE_VOCABULARY
    }

    mapped = {
        mapping.event_type
        for mapping in EVIDENCE_FEATURE_MAPPINGS
    }

    assert mapped == vocabulary


def test_exactly_five_compatible_mappings():
    compatible = [
        mapping
        for mapping in EVIDENCE_FEATURE_MAPPINGS
        if mapping.status == "compatible_with_constraints"
    ]

    assert len(compatible) == 5


def test_exactly_seven_unresolved_mappings():
    unresolved = [
        mapping
        for mapping in EVIDENCE_FEATURE_MAPPINGS
        if mapping.status == "requires_semantic_refinement"
    ]

    assert len(unresolved) == 7


def test_only_supported_statuses_are_used():
    allowed = {
        "compatible_with_constraints",
        "requires_semantic_refinement",
    }

    assert all(
        mapping.status in allowed
        for mapping in EVIDENCE_FEATURE_MAPPINGS
    )


def test_compatible_mappings_have_attribute_names():
    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.status == "compatible_with_constraints":
            assert mapping.attribute_name


def test_compatible_mappings_have_feature_names():
    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.status == "compatible_with_constraints":
            assert mapping.feature_name


def test_unresolved_mappings_have_no_attribute():
    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.status == "requires_semantic_refinement":
            assert mapping.attribute_name is None


def test_unresolved_mappings_have_no_feature():
    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.status == "requires_semantic_refinement":
            assert mapping.feature_name is None


def test_all_mappings_have_explanations():
    assert all(
        mapping.explanation
        for mapping in EVIDENCE_FEATURE_MAPPINGS
    )


def test_file_write_mapping():
    mapping = get_cycle3_evidence_feature_mapping(
        "file_write_activity"
    )

    assert mapping.attribute_name == "write_count"
    assert mapping.feature_name == "write_rate"
    assert mapping.status == "compatible_with_constraints"


def test_file_rename_mapping():
    mapping = get_cycle3_evidence_feature_mapping(
        "file_rename_activity"
    )

    assert mapping.attribute_name == "rename_count"
    assert mapping.feature_name == "rename_rate"


def test_service_state_mapping():
    mapping = get_cycle3_evidence_feature_mapping(
        "service_state_observation"
    )

    assert mapping.attribute_name == "service_available"
    assert mapping.feature_name == "service_availability_ratio"


def test_telemetry_freshness_mapping():
    mapping = get_cycle3_evidence_feature_mapping(
        "telemetry_freshness_observation"
    )

    assert mapping.attribute_name == "ingestion_lag_seconds"
    assert mapping.feature_name == "ingestion_lag_seconds"


def test_maintenance_authorization_mapping():
    mapping = get_cycle3_evidence_feature_mapping(
        "maintenance_authorization_observation"
    )

    assert mapping.attribute_name is None
    assert mapping.feature_name is None
    assert mapping.status == "requires_semantic_refinement"
    assert "denominator" in mapping.explanation.lower()


def test_authentication_activity_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "authentication_activity"
    )

    assert mapping.status == "requires_semantic_refinement"
    assert mapping.attribute_name is None
    assert mapping.feature_name is None


def test_remote_session_activity_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "remote_session_activity"
    )

    assert mapping.status == "requires_semantic_refinement"


def test_network_peer_activity_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "network_peer_activity"
    )

    assert mapping.status == "requires_semantic_refinement"


def test_backup_status_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "backup_status_observation"
    )

    assert mapping.status == "requires_semantic_refinement"


def test_restore_test_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "restore_test_observation"
    )

    assert mapping.status == "requires_semantic_refinement"


def test_communications_state_is_unresolved():
    mapping = get_cycle3_evidence_feature_mapping(
        "communications_state_observation"
    )

    assert mapping.status == "requires_semantic_refinement"


def test_unknown_event_type_is_rejected():
    with pytest.raises(KeyError):
        get_cycle3_evidence_feature_mapping(
            "unknown_observation"
        )


def test_mapping_validation_passes():
    assert validate_cycle3_evidence_feature_mappings() is None


def test_mapping_is_immutable():
    mapping = EVIDENCE_FEATURE_MAPPINGS[0]

    with pytest.raises(FrozenInstanceError):
        mapping.status = "modified"


def test_mapping_collection_is_tuple():
    assert isinstance(EVIDENCE_FEATURE_MAPPINGS, tuple)


def test_lookup_is_deterministic():
    first = get_cycle3_evidence_feature_mapping(
        "file_write_activity"
    )

    second = get_cycle3_evidence_feature_mapping(
        "file_write_activity"
    )

    assert first == second


def test_replacement_does_not_mutate_original():
    original = EVIDENCE_FEATURE_MAPPINGS[0]

    modified = replace(
        original,
        explanation="Modified test explanation",
    )

    assert original.explanation != modified.explanation
    assert original.event_type == modified.event_type


@pytest.mark.parametrize(
    "event_type",
    [
        "privilege_change_activity",
        "file_write_activity",
        "file_rename_activity",
        "service_state_observation",
        "telemetry_freshness_observation",
    ],
)
def test_compatible_mapping_lookup(event_type):
    mapping = get_cycle3_evidence_feature_mapping(event_type)

    assert mapping.status == "compatible_with_constraints"
    assert mapping.attribute_name is not None
    assert mapping.feature_name is not None


@pytest.mark.parametrize(
    "event_type",
    [
        "authentication_activity",
        "remote_session_activity",
        "network_peer_activity",
        "backup_status_observation",
        "restore_test_observation",
        "communications_state_observation",
    ],
)
def test_unresolved_mapping_lookup(event_type):
    mapping = get_cycle3_evidence_feature_mapping(event_type)

    assert mapping.status == "requires_semantic_refinement"
    assert mapping.attribute_name is None
    assert mapping.feature_name is None
