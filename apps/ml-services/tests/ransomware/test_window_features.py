from __future__ import annotations

from datetime import datetime, timezone

import pytest

from config.ransomware.features.window_features import (
    EVIDENCE_DOMAINS,
    WINDOW_MINUTES,
    extract_window_feature_series,
    extract_window_features,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


def _event(
    minute: int,
    family: str,
    event_type: str,
    asset_id: str = "asset-1",
    attributes: dict[str, object] | None = None,
) -> ObservableScenarioEvent:
    return ObservableScenarioEvent(
        scenario_id="synthetic-test-scenario",
        scenario_seed=123,
        split="train",
        sequence_index=minute,
        event_time=(
            datetime(
                2026,
                1,
                1,
                6,
                minute,
                tzinfo=timezone.utc,
            )
            .isoformat()
            .replace("+00:00", "Z")
        ),
        event_family=family,
        event_type=event_type,
        asset_id=asset_id,
        attributes=attributes or {},
    )


def test_rw0601_declares_required_domains_and_windows() -> None:
    assert WINDOW_MINUTES == (1, 5, 15)

    assert set(EVIDENCE_DOMAINS) == {
        "identity",
        "endpoint",
        "file",
        "network",
        "backup",
        "service",
        "asset",
        "graph",
        "context",
        "quality",
    }


def test_rw0601_extracts_observable_domain_features() -> None:
    events = [
        _event(
            0,
            "file",
            "file_write_spike",
            attributes={"value": 0.8},
        ),
        _event(
            0,
            "remote",
            "remote_sessions",
            attributes={
                "evidence_name": "remote_sessions",
                "observable_value": 0.7,
            },
        ),
        _event(
            0,
            "backup",
            "backup_coverage",
            attributes={
                "evidence_name": "backup_coverage",
                "observable_value": 0.6,
            },
        ),
        _event(
            0,
            "service",
            "service_state",
            attributes={
                "evidence_name": "service_state",
                "observable_value": 0.5,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["event_count"] == 4
    assert features["file_evidence_count"] == 1
    assert features["network_evidence_count"] == 1
    assert features["backup_evidence_count"] == 1
    assert features["service_evidence_count"] == 1
    assert features["observable_value_max"] == 0.8


def test_rw0601_generates_all_three_window_sizes() -> None:
    events = [
        _event(
            0,
            "file",
            "file_write_spike",
            attributes={"value": 0.8},
        ),
        _event(
            1,
            "backup",
            "backup_coverage",
            attributes={
                "evidence_name": "backup_coverage",
                "observable_value": 0.6,
            },
        ),
        _event(
            5,
            "service",
            "service_state",
            attributes={
                "evidence_name": "service_state",
                "observable_value": 0.5,
            },
        ),
    ]

    rows = extract_window_feature_series(events)

    assert len(rows) == len(events) * 3

    observed_windows = {
        row["window_duration_minutes"]
        for row in rows
    }

    assert observed_windows == {1, 5, 15}


def test_rw0601_rejects_unsupported_window_size() -> None:
    events = [
        _event(
            0,
            "file",
            "file_write_spike",
            attributes={"value": 0.8},
        )
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported feature window",
    ):
        extract_window_features(
            events,
            end_time,
            10,
        )


def test_rw0602_identity_features_manual_one_minute_window() -> None:
    events = [
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-a",
                "new_source_relationship": True,
                "privilege_change": False,
            },
        ),
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-b",
                "new_source_relationship": False,
                "privilege_change": True,
            },
        ),
        _event(
            0,
            "identity",
            "authentication_success",
            attributes={
                "auth_failure": False,
                "source_host": "host-a",
                "new_source_relationship": True,
                "privilege_change": False,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["auth_failure_count"] == 2
    assert features["distinct_source_host_count"] == 2
    assert features["new_source_relationship_count"] == 2
    assert features["privilege_change_count"] == 1


def test_rw0602_identity_features_include_five_minute_boundary() -> None:
    events = [
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-a",
                "new_source_relationship": True,
                "privilege_change": False,
            },
        ),
        _event(
            5,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-b",
                "new_source_relationship": False,
                "privilege_change": True,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        5,
    )

    assert features["auth_failure_count"] == 2
    assert features["distinct_source_host_count"] == 2
    assert features["new_source_relationship_count"] == 1
    assert features["privilege_change_count"] == 1


def test_rw0602_identity_features_exclude_event_outside_window() -> None:
    events = [
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-a",
                "new_source_relationship": True,
                "privilege_change": True,
            },
        ),
        _event(
            5,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-b",
                "new_source_relationship": False,
                "privilege_change": False,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["auth_failure_count"] == 1
    assert features["distinct_source_host_count"] == 1
    assert features["new_source_relationship_count"] == 0
    assert features["privilege_change_count"] == 0


def test_rw0603_endpoint_file_features_manual_window() -> None:
    events = [
        _event(
            0,
            "endpoint",
            "process_chain",
            attributes={
                "rare_process_chain": True,
                "unsigned_process": True,
                "task_service_created": True,
                "write_count": 10,
                "rename_count": 4,
                "extension_change_count": 2,
                "file_event_count": 4,
                "entropy_proxy": 0.8,
            },
        ),
        _event(
            0,
            "endpoint",
            "process_chain",
            attributes={
                "rare_process_chain": True,
                "unsigned_process": True,
                "task_service_created": False,
                "write_count": 5,
                "rename_count": 2,
                "extension_change_count": 1,
                "file_event_count": 2,
                "entropy_proxy": 0.6,
            },
        ),
        _event(
            0,
            "endpoint",
            "process_chain",
            attributes={
                "rare_process_chain": False,
                "unsigned_process": False,
                "task_service_created": False,
                "write_count": 3,
                "rename_count": 0,
                "extension_change_count": 0,
                "file_event_count": 2,
                "entropy_proxy": 0.4,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["rare_process_chain_score"] == 0.666667
    assert features["unsigned_burst_count"] == 2
    assert features["task_service_creation_count"] == 1
    assert features["write_rate"] == 18
    assert features["rename_rate"] == 6
    assert features["extension_change_ratio"] == 0.375
    assert features["entropy_proxy"] == 0.6


def test_rw0603_endpoint_file_features_respect_five_minute_window() -> None:
    events = [
        _event(
            0,
            "file",
            "file_activity",
            attributes={
                "rare_process_chain": True,
                "write_count": 10,
                "rename_count": 4,
                "extension_change_count": 2,
                "file_event_count": 4,
                "entropy_proxy": 0.8,
            },
        ),
        _event(
            5,
            "file",
            "file_activity",
            attributes={
                "rare_process_chain": False,
                "write_count": 5,
                "rename_count": 1,
                "extension_change_count": 1,
                "file_event_count": 2,
                "entropy_proxy": 0.4,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        5,
    )

    assert features["rare_process_chain_score"] == 0.5
    assert features["write_rate"] == 3
    assert features["rename_rate"] == 1
    assert features["extension_change_ratio"] == 0.5
    assert features["entropy_proxy"] == 0.6


def test_rw0603_endpoint_file_features_exclude_event_outside_window() -> None:
    events = [
        _event(
            0,
            "file",
            "file_activity",
            attributes={
                "rare_process_chain": True,
                "write_count": 100,
                "rename_count": 100,
                "extension_change_count": 100,
                "file_event_count": 100,
                "entropy_proxy": 1.0,
            },
        ),
        _event(
            5,
            "file",
            "file_activity",
            attributes={
                "rare_process_chain": False,
                "write_count": 5,
                "rename_count": 2,
                "extension_change_count": 1,
                "file_event_count": 4,
                "entropy_proxy": 0.4,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["rare_process_chain_score"] == 0
    assert features["write_rate"] == 5
    assert features["rename_rate"] == 2
    assert features["extension_change_ratio"] == 0.25
    assert features["entropy_proxy"] == 0.4


def test_rw0604_network_backup_service_features_manual_window() -> None:
    events = [
        _event(
            0,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 4,
                "new_peer_count": 2,
                "zone_crossing": True,
                "outbound_bytes": 5000,
            },
        ),
        _event(
            0,
            "backup",
            "backup_health",
            attributes={
                "backup_age_minutes": 120,
                "backup_failure_streak": 2,
                "immutable_copy": True,
                "restore_test_age_days": 10,
            },
        ),
        _event(
            0,
            "service",
            "service_state",
            attributes={
                "service_available": True,
                "ingestion_lag_seconds": 30,
                "stale_data": False,
            },
        ),
        _event(
            0,
            "service",
            "service_state",
            attributes={
                "service_available": False,
                "ingestion_lag_seconds": 60,
                "stale_data": True,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["remote_admin_peer_count"] == 4
    assert features["new_peer_ratio"] == 0.5
    assert features["zone_crossing_count"] == 1
    assert features["outbound_bytes"] == 5000

    assert features["backup_age_minutes"] == 120
    assert features["backup_failure_streak"] == 2
    assert features["immutable_copy_present_count"] == 1
    assert features["restore_test_age_days"] == 10

    assert features["service_availability_ratio"] == 0.5
    assert features["ingestion_lag_seconds"] == 60
    assert features["stale_data_ratio"] == 0.5


def test_rw0604_network_backup_service_features_respect_five_minute_window() -> None:
    events = [
        _event(
            0,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 2,
                "new_peer_count": 1,
                "zone_crossing": True,
                "outbound_bytes": 1000,
            },
        ),
        _event(
            1,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 4,
                "new_peer_count": 2,
                "zone_crossing": False,
                "outbound_bytes": 2000,
            },
        ),
        _event(
            5,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 4,
                "new_peer_count": 1,
                "zone_crossing": True,
                "outbound_bytes": 3000,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        5,
    )

    assert features["remote_admin_peer_count"] == 10
    assert features["new_peer_ratio"] == 0.4
    assert features["zone_crossing_count"] == 2
    assert features["outbound_bytes"] == 6000


def test_rw0604_network_backup_service_features_exclude_event_outside_window() -> None:
    events = [
        _event(
            0,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 10,
                "new_peer_count": 10,
                "zone_crossing": True,
                "outbound_bytes": 10000,
            },
        ),
        _event(
            5,
            "network",
            "network_activity",
            attributes={
                "remote_admin_peer_count": 2,
                "new_peer_count": 1,
                "zone_crossing": True,
                "outbound_bytes": 500,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["remote_admin_peer_count"] == 2
    assert features["new_peer_ratio"] == 0.5
    assert features["zone_crossing_count"] == 1
    assert features["outbound_bytes"] == 500


def test_rw0605_graph_context_quality_features_manual_window() -> None:
    events = [
        _event(
            0,
            "asset",
            "asset_context",
            attributes={
                "criticality_score": 1.0,
                "recovery_tier": 1,
            },
        ),
        _event(
            0,
            "graph",
            "boundary_path",
            attributes={
                "protected_boundary_hops": 2,
                "critical_service_exposure": True,
            },
        ),
        _event(
            0,
            "context",
            "maintenance",
            attributes={
                "maintenance_approved": True,
            },
        ),
        _event(
            0,
            "quality",
            "source_quality",
            attributes={
                "missing_source": True,
                "late_event": False,
                "stage_transition_score": 0.25,
            },
        ),
        _event(
            0,
            "quality",
            "source_quality",
            attributes={
                "missing_source": False,
                "late_event": True,
                "stage_transition_score": 0.75,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["criticality_score"] == 1.0
    assert features["recovery_tier"] == 1
    assert features["protected_boundary_hops"] == 2
    assert features["critical_service_exposure_count"] == 1
    assert features["maintenance_approval_ratio"] == 0.2
    assert features["missing_source_mask"] == 1
    assert features["late_event_ratio"] == 0.2
    assert features["stage_transition_score"] == 0.5


def test_rw0605_graph_context_quality_features_respect_five_minute_window() -> None:
    events = [
        _event(
            0,
            "graph",
            "boundary_path",
            attributes={
                "criticality_score": 0.8,
                "recovery_tier": 2,
                "protected_boundary_hops": 1,
                "critical_service_exposure": True,
            },
        ),
        _event(
            1,
            "context",
            "maintenance",
            attributes={
                "maintenance_approved": True,
            },
        ),
        _event(
            5,
            "quality",
            "source_quality",
            attributes={
                "missing_source": True,
                "late_event": True,
                "stage_transition_score": 0.6,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        5,
    )

    assert features["criticality_score"] == 0.8
    assert features["recovery_tier"] == 2
    assert features["protected_boundary_hops"] == 1
    assert features["critical_service_exposure_count"] == 1
    assert features["maintenance_approval_ratio"] == 0.333333
    assert features["missing_source_mask"] == 1
    assert features["late_event_ratio"] == 0.333333
    assert features["stage_transition_score"] == 0.6


def test_rw0605_graph_context_quality_features_exclude_event_outside_window() -> None:
    events = [
        _event(
            0,
            "graph",
            "boundary_path",
            attributes={
                "criticality_score": 1.0,
                "recovery_tier": 1,
                "protected_boundary_hops": 10,
                "critical_service_exposure": True,
            },
        ),
        _event(
            5,
            "graph",
            "boundary_path",
            attributes={
                "criticality_score": 0.5,
                "recovery_tier": 3,
                "protected_boundary_hops": 2,
                "critical_service_exposure": False,
            },
        ),
    ]

    end_time = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    assert features["criticality_score"] == 0.5
    assert features["recovery_tier"] == 3
    assert features["protected_boundary_hops"] == 2
    assert features["critical_service_exposure_count"] == 0

def test_rw0606_energy_sector_extensions():
    events = [
        _event(
            0,
            "service",
            "service_state",
            attributes={
                "evidence_name": "service_state",
                "observable_available": True,
            },
        ),
        _event(
            0,
            "quality",
            "ingestion_lag",
            attributes={
                "evidence_name": "ingestion_lag",
                "observable_available": True,
            },
        ),
        _event(
            0,
            "network",
            "remote_sessions",
            attributes={
                "evidence_name": "remote_sessions",
            },
        ),
        _event(
            0,
            "network",
            "protected_zone_adjacency",
            attributes={
                "evidence_name": "protected_zone_adjacency",
            },
        ),
        _event(
            0,
            "file",
            "configuration_package_access",
            attributes={
                "evidence_name": "configuration_package_access",
            },
        ),
        _event(
            1,
            "network",
            "communications_health",
            attributes={
                "evidence_name": "communications_health",
                "communications_available": True,
            },
        ),
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            1,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["scada_visibility_ratio"] == 1.0
    assert features["substation_support_exposure_count"] == 3
    assert features["relay_management_adjacency_count"] == 2
    assert features["communications_health_ratio"] == 1.0


def test_rw0606_missing_energy_evidence_is_explicit():
    events = [
        _event(
            0,
            "identity",
            "authentication_fan_out",
            attributes={
                "evidence_name": "authentication_fan_out",
            },
        )
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            1,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["scada_visibility_ratio"] == 0.0
    assert features["substation_support_exposure_count"] == 0
    assert features["relay_management_adjacency_count"] == 0
    assert features["communications_health_ratio"] == 0.0


def test_rw0607_petrochemical_sector_extensions():
    events = [
        _event(
            0,
            "file",
            "project_file_access",
            attributes={"evidence_name": "project_file_access"},
        ),
        _event(
            0,
            "endpoint",
            "configuration_activity",
            attributes={"evidence_name": "configuration_activity"},
        ),
        _event(
            0,
            "service",
            "alarm_support_availability",
            attributes={
                "evidence_name": "alarm_support_availability",
                "service_available": True,
            },
        ),
        _event(
            0,
            "network",
            "engineering_access",
            attributes={"evidence_name": "engineering_access"},
        ),
        _event(
            0,
            "network",
            "protected_zone_adjacency",
            attributes={"evidence_name": "protected_zone_adjacency"},
        ),
        _event(
            0,
            "quality",
            "batch_event_gaps",
            attributes={"evidence_name": "batch_event_gaps"},
        ),
        _event(
            0,
            "service",
            "database_health",
            attributes={"evidence_name": "database_health"},
        ),
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["dcs_support_exposure_count"] == 2
    assert features["alarm_support_health_ratio"] == 1.0
    assert features["sis_esd_adjacency_count"] == 2
    assert features["batch_quality_dependency_exposure_count"] == 2


def test_rw0607_missing_petrochemical_evidence_is_explicit():
    events = [
        _event(
            0,
            "identity",
            "authentication_fan_out",
            attributes={
                "evidence_name": "authentication_fan_out",
            },
        )
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["dcs_support_exposure_count"] == 0
    assert features["alarm_support_health_ratio"] == 0.0
    assert features["sis_esd_adjacency_count"] == 0
    assert features["batch_quality_dependency_exposure_count"] == 0


def test_rw0607_petrochemical_sector_extensions():
    events = [
        _event(
            0,
            "file",
            "project_file_access",
            attributes={"evidence_name": "project_file_access"},
        ),
        _event(
            0,
            "endpoint",
            "configuration_activity",
            attributes={"evidence_name": "configuration_activity"},
        ),
        _event(
            0,
            "service",
            "alarm_support_availability",
            attributes={
                "evidence_name": "alarm_support_availability",
                "service_available": True,
            },
        ),
        _event(
            0,
            "network",
            "engineering_access",
            attributes={"evidence_name": "engineering_access"},
        ),
        _event(
            0,
            "network",
            "protected_zone_adjacency",
            attributes={"evidence_name": "protected_zone_adjacency"},
        ),
        _event(
            0,
            "quality",
            "batch_event_gaps",
            attributes={"evidence_name": "batch_event_gaps"},
        ),
        _event(
            0,
            "service",
            "database_health",
            attributes={"evidence_name": "database_health"},
        ),
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["dcs_support_exposure_count"] == 2
    assert features["alarm_support_health_ratio"] == 1.0
    assert features["sis_esd_adjacency_count"] == 2
    assert features["batch_quality_dependency_exposure_count"] == 2


def test_rw0607_missing_petrochemical_evidence_is_explicit():
    events = [
        _event(
            0,
            "identity",
            "authentication_fan_out",
            attributes={
                "evidence_name": "authentication_fan_out",
            },
        )
    ]

    features = extract_window_features(
        events,
        datetime(
            2026,
            1,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        ),
        1,
    )

    assert features["dcs_support_exposure_count"] == 0
    assert features["alarm_support_health_ratio"] == 0.0
    assert features["sis_esd_adjacency_count"] == 0
    assert features["batch_quality_dependency_exposure_count"] == 0
