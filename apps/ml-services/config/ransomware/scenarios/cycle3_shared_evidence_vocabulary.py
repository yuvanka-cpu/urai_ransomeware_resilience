"""Shared observable evidence vocabulary for Cycle 3.

Development-only design contract.

Event names describe observations, not scenario labels.
This module does not generate events, modify historical data,
train models, or execute industrial actions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cycle3EvidenceDefinition:
    event_type: str
    evidence_domain: str
    measurement_kind: str
    unit: str | None
    description: str


SHARED_EVIDENCE_VOCABULARY = (
    Cycle3EvidenceDefinition(
        event_type="authentication_activity",
        evidence_domain="identity",
        measurement_kind="count",
        unit="events",
        description="Observed authentication activity within a window.",
    ),
    Cycle3EvidenceDefinition(
        event_type="privilege_change_activity",
        evidence_domain="identity",
        measurement_kind="boolean",
        unit=None,
        description="Whether a privilege-change occurrence was observed.",
    ),
    Cycle3EvidenceDefinition(
        event_type="remote_session_activity",
        evidence_domain="network",
        measurement_kind="count",
        unit="sessions",
        description="Observed remote administration sessions.",
    ),
    Cycle3EvidenceDefinition(
        event_type="network_peer_activity",
        evidence_domain="network",
        measurement_kind="count",
        unit="peers",
        description="Observed network peer relationships.",
    ),
    Cycle3EvidenceDefinition(
        event_type="file_write_activity",
        evidence_domain="file",
        measurement_kind="count",
        unit="operations",
        description="Observed file-write operations.",
    ),
    Cycle3EvidenceDefinition(
        event_type="file_rename_activity",
        evidence_domain="file",
        measurement_kind="count",
        unit="operations",
        description="Observed file-rename operations.",
    ),
    Cycle3EvidenceDefinition(
        event_type="service_state_observation",
        evidence_domain="service_health",
        measurement_kind="boolean",
        unit=None,
        description="Observed service availability state.",
    ),
    Cycle3EvidenceDefinition(
        event_type="backup_status_observation",
        evidence_domain="backup",
        measurement_kind="boolean",
        unit=None,
        description="Observed backup health state.",
    ),
    Cycle3EvidenceDefinition(
        event_type="restore_test_observation",
        evidence_domain="recovery",
        measurement_kind="boolean",
        unit=None,
        description="Observed restore-test outcome.",
    ),
    Cycle3EvidenceDefinition(
        event_type="telemetry_freshness_observation",
        evidence_domain="telemetry_quality",
        measurement_kind="duration",
        unit="seconds",
        description="Observed telemetry ingestion lag.",
    ),
    Cycle3EvidenceDefinition(
        event_type="communications_state_observation",
        evidence_domain="communications",
        measurement_kind="boolean",
        unit=None,
        description="Observed communications availability.",
    ),
    Cycle3EvidenceDefinition(
        event_type="maintenance_authorization_observation",
        evidence_domain="maintenance",
        measurement_kind="boolean",
        unit=None,
        description="Observed maintenance authorization status.",
    ),
)


def get_cycle3_evidence_definition(
    event_type: str,
) -> Cycle3EvidenceDefinition:
    """Resolve one shared observable evidence definition."""

    for definition in SHARED_EVIDENCE_VOCABULARY:
        if definition.event_type == event_type:
            return definition

    raise KeyError(
        f"Unknown Cycle 3 shared evidence type: {event_type}"
    )


def validate_cycle3_evidence_vocabulary() -> None:
    """Check vocabulary uniqueness and measurement metadata."""

    names = [
        definition.event_type
        for definition in SHARED_EVIDENCE_VOCABULARY
    ]

    if len(names) != len(set(names)):
        raise ValueError("Duplicate shared evidence event types")

    allowed_kinds = {"count", "boolean", "duration"}

    for definition in SHARED_EVIDENCE_VOCABULARY:
        if not definition.event_type:
            raise ValueError("Empty event type")

        if not definition.evidence_domain:
            raise ValueError("Empty evidence domain")

        if definition.measurement_kind not in allowed_kinds:
            raise ValueError("Unsupported measurement kind")

        if definition.measurement_kind == "boolean":
            if definition.unit is not None:
                raise ValueError(
                    "Boolean measurements must not declare units"
                )
        elif not definition.unit:
            raise ValueError(
                "Numeric measurements require explicit units"
            )
