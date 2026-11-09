"""Cycle 3 shared-evidence to feature compatibility contract.

Development-only metadata. No synthetic measurements are generated here.

Mappings describe compatible attribute semantics, not proof that a
measurement was observed or that a feature is statistically valid.
"""

from dataclasses import dataclass

from config.ransomware.shared.validation.canonical_feature_units import (
    CANONICAL_FEATURE_UNITS,
)

from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    SHARED_EVIDENCE_VOCABULARY,
    get_cycle3_evidence_definition,
)


@dataclass(frozen=True)
class Cycle3EvidenceFeatureMapping:
    event_type: str
    attribute_name: str | None
    feature_name: str | None
    status: str
    explanation: str
    source_unit: str | None = None
    feature_unit: str | None = None
    transformation: str | None = None


EXPECTED_COMPATIBLE_MAPPING_CONTRACTS = {
    "privilege_change_activity": (
        "privilege_change_count",
        "count",
        "count_true_occurrences",
    ),
    "file_write_activity": (
        "write_rate",
        "operations/minute",
        "divide_by_window_duration_minutes",
    ),
    "file_rename_activity": (
        "rename_rate",
        "operations/minute",
        "divide_by_window_duration_minutes",
    ),
    "service_state_observation": (
        "service_availability_ratio",
        "ratio",
        "available_over_observed_service_events",
    ),
    "telemetry_freshness_observation": (
        "ingestion_lag_seconds",
        "seconds",
        "maximum_observed_lag",
    ),
}


EVIDENCE_FEATURE_MAPPINGS = (
    Cycle3EvidenceFeatureMapping(
        "authentication_activity",
        None,
        None,
        "requires_semantic_refinement",
        "Total authentication activity is not equivalent to auth failures.",
    ),
    Cycle3EvidenceFeatureMapping(
        "privilege_change_activity",
        "privilege_change",
        "privilege_change_count",
        "compatible_with_constraints",
        "One observed privilege-change occurrence maps to True.",
        source_unit=None,
        feature_unit="count",
        transformation="count_true_occurrences",
    ),
    Cycle3EvidenceFeatureMapping(
        "remote_session_activity",
        None,
        None,
        "requires_semantic_refinement",
        "Session count is not necessarily distinct remote-admin peer count.",
    ),
    Cycle3EvidenceFeatureMapping(
        "network_peer_activity",
        None,
        None,
        "requires_semantic_refinement",
        "Observed peers are not necessarily new peers.",
    ),
    Cycle3EvidenceFeatureMapping(
        "file_write_activity",
        "write_count",
        "write_rate",
        "compatible_with_constraints",
        "Observed write-operation count; extractor divides by window minutes.",
        source_unit="operations",
        feature_unit="operations/minute",
        transformation="divide_by_window_duration_minutes",
    ),
    Cycle3EvidenceFeatureMapping(
        "file_rename_activity",
        "rename_count",
        "rename_rate",
        "compatible_with_constraints",
        "Observed rename-operation count; extractor divides by window minutes.",
        source_unit="operations",
        feature_unit="operations/minute",
        transformation="divide_by_window_duration_minutes",
    ),
    Cycle3EvidenceFeatureMapping(
        "service_state_observation",
        "service_available",
        "service_availability_ratio",
        "compatible_with_constraints",
        "Boolean service availability; missing observations must remain distinct.",
        source_unit=None,
        feature_unit="ratio",
        transformation="available_over_observed_service_events",
    ),
    Cycle3EvidenceFeatureMapping(
        "backup_status_observation",
        None,
        None,
        "requires_semantic_refinement",
        "Generic backup health is not equivalent to immutable-copy presence.",
    ),
    Cycle3EvidenceFeatureMapping(
        "restore_test_observation",
        None,
        None,
        "requires_semantic_refinement",
        "Restore-test outcome is not equivalent to restore-test age.",
    ),
    Cycle3EvidenceFeatureMapping(
        "telemetry_freshness_observation",
        "ingestion_lag_seconds",
        "ingestion_lag_seconds",
        "compatible_with_constraints",
        "Nonnegative measured ingestion lag in seconds.",
        source_unit="seconds",
        feature_unit="seconds",
        transformation="maximum_observed_lag",
    ),
    Cycle3EvidenceFeatureMapping(
        "communications_state_observation",
        None,
        None,
        "requires_semantic_refinement",
        "Communications availability needs an explicit evidence-ratio contract.",
    ),
    Cycle3EvidenceFeatureMapping(
        "maintenance_authorization_observation",
        None,
        None,
        "requires_semantic_refinement",
        "Existing extractor divides approved observations by all window events; maintenance-specific denominator semantics remain unresolved.",
    ),
)


def get_cycle3_evidence_feature_mapping(
    event_type: str,
) -> Cycle3EvidenceFeatureMapping:
    """Return the mapping for one known shared evidence type."""

    get_cycle3_evidence_definition(event_type)

    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.event_type == event_type:
            return mapping

    raise KeyError(
        f"No Cycle 3 feature mapping for: {event_type}"
    )


def validate_cycle3_evidence_feature_mappings() -> None:
    """Validate mapping coverage and compatibility metadata."""

    vocabulary_names = {
        definition.event_type
        for definition in SHARED_EVIDENCE_VOCABULARY
    }

    mapping_names = [
        mapping.event_type
        for mapping in EVIDENCE_FEATURE_MAPPINGS
    ]

    if len(mapping_names) != len(set(mapping_names)):
        raise ValueError("Duplicate evidence-feature mappings")

    if set(mapping_names) != vocabulary_names:
        raise ValueError("Evidence-feature mapping coverage mismatch")

    allowed_statuses = {
        "compatible_with_constraints",
        "requires_semantic_refinement",
    }

    definitions = {
        definition.event_type: definition
        for definition in SHARED_EVIDENCE_VOCABULARY
    }

    for mapping in EVIDENCE_FEATURE_MAPPINGS:
        if mapping.status not in allowed_statuses:
            raise ValueError("Unsupported mapping status")

        if not mapping.explanation:
            raise ValueError("Missing mapping explanation")

        if mapping.status == "compatible_with_constraints":
            if not mapping.attribute_name or not mapping.feature_name:
                raise ValueError(
                    "Compatible mapping requires attribute and feature"
                )
            definition = definitions[mapping.event_type]
            if mapping.source_unit != definition.unit:
                raise ValueError(
                    f"Source unit mismatch for {mapping.event_type!r}"
                )
            if not mapping.feature_unit or not mapping.transformation:
                raise ValueError(
                    f"Missing unit or transformation for {mapping.event_type!r}"
                )

            expected_contract = EXPECTED_COMPATIBLE_MAPPING_CONTRACTS.get(
                mapping.event_type
            )
            actual_contract = (
                mapping.feature_name,
                mapping.feature_unit,
                mapping.transformation,
            )
            if actual_contract != expected_contract:
                raise ValueError(
                    f"Feature unit or transformation contract mismatch "
                    f"for {mapping.event_type!r}"
                )

            registered_unit = CANONICAL_FEATURE_UNITS.get(
                mapping.feature_name
            )
            if (
                registered_unit is not None
                and registered_unit != mapping.feature_unit
            ):
                raise ValueError(
                    f"Feature unit mismatch for {mapping.feature_name!r}"
                )

        if mapping.status == "requires_semantic_refinement":
            if mapping.attribute_name is not None:
                raise ValueError(
                    "Unresolved mapping must not declare an attribute"
                )

            if mapping.feature_name is not None:
                raise ValueError(
                    "Unresolved mapping must not declare a feature"
                )
            if any((
                mapping.source_unit,
                mapping.feature_unit,
                mapping.transformation,
            )):
                raise ValueError(
                    "Unresolved mapping must not declare unit or transformation metadata"
                )
