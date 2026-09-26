from datetime import datetime, timedelta, timezone

import pytest

from config.ransomware.features.feature_parity import (
    DEFAULT_FEATURE_TOLERANCE,
    compare_feature_rows,
    compute_offline_features,
    compute_online_features,
)


PARTITION = (
    "energy-blr01+energy-blr01-asset-scada-support-001"
)


def _canonical_event(
    event_id: str,
    minute: int,
    event_family: str,
    event_type: str,
    attributes: dict[str, object],
    ingest_second: int,
):
    return {
        "event_id": event_id,
        "event_time": (
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
        "ingest_time": (
            datetime(
                2026,
                1,
                1,
                6,
                minute,
                ingest_second,
                tzinfo=timezone.utc,
            )
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-scada-support-001",
        "event_family": event_family,
        "event_type": event_type,
        "attributes": attributes,
    }


def _fixture_events():
    return [
        _canonical_event(
            "evt-001",
            0,
            "identity",
            "authentication_fan_out",
            {
                "evidence_name": "authentication_fan_out",
                "auth_failure": True,
                "source_host": "host-a",
                "new_source_relationship": True,
                "privilege_change": True,
                "observable_value": 2.0,
            },
            1,
        ),
        _canonical_event(
            "evt-002",
            1,
            "endpoint",
            "process_chain",
            {
                "evidence_name": "process_parent_relationships",
                "rare_process_chain": True,
                "unsigned_process": True,
                "task_service_creation": True,
                "observable_value": 3.0,
            },
            1,
        ),
        _canonical_event(
            "evt-003",
            2,
            "file",
            "file_write",
            {
                "evidence_name": "file_write_rate",
                "write_count": 10,
                "rename_count": 2,
                "extension_change": True,
                "entropy_proxy": 0.8,
                "observable_value": 4.0,
            },
            1,
        ),
        _canonical_event(
            "evt-004",
            3,
            "network",
            "remote_session",
            {
                "evidence_name": "remote_sessions",
                "remote_admin": True,
                "new_peer": True,
                "zone_crossing": True,
                "outbound_bytes": 2048,
                "protected_boundary_hops": 1,
                "critical_service_exposure": True,
            },
            1,
        ),
        _canonical_event(
            "evt-005",
            4,
            "backup",
            "backup_health",
            {
                "evidence_name": "backup_age",
                "backup_age_minutes": 12,
                "backup_failure": True,
                "immutable_copy_present": True,
                "restore_test_age_days": 4,
            },
            1,
        ),
        _canonical_event(
            "evt-006",
            5,
            "service",
            "service_state",
            {
                "evidence_name": "service_state",
                "service_available": True,
                "criticality_score": 5,
                "recovery_tier": 2,
            },
            1,
        ),
        _canonical_event(
            "evt-007",
            5,
            "network",
            "communications_health",
            {
                "evidence_name": "communications_health",
                "communications_available": True,
                "observable_available": True,
            },
            2,
        ),
        _canonical_event(
            "evt-008",
            5,
            "file",
            "configuration_package_access",
            {
                "evidence_name": "configuration_package_access",
                "maintenance_approved": True,
            },
            3,
        ),
    ]


def test_rw0609_offline_online_feature_parity():
    events = _fixture_events()

    anchor = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    offline = compute_offline_features(
        events,
        partition_key=PARTITION,
        anchor_time=anchor,
        window_minutes=5,
    )

    online, replay_ids = compute_online_features(
        list(reversed(events)),
        partition_key=PARTITION,
        anchor_time=anchor,
        window_minutes=5,
        allowed_lateness=timedelta(minutes=5),
    )

    parity = compare_feature_rows(
        offline,
        online,
        tolerance=DEFAULT_FEATURE_TOLERANCE,
    )

    assert parity.passed
    assert parity.compared_fields == len(offline)
    assert parity.compared_fields == len(online)
    assert parity.mismatches == ()
    assert replay_ids == ()


def test_rw0609_identical_replay_preserves_parity():
    events = _fixture_events()
    replayed = list(reversed(events))
    replayed.append(dict(events[3]))

    anchor = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    offline = compute_offline_features(
        events,
        partition_key=PARTITION,
        anchor_time=anchor,
        window_minutes=5,
    )

    online, replay_ids = compute_online_features(
        replayed,
        partition_key=PARTITION,
        anchor_time=anchor,
        window_minutes=5,
        allowed_lateness=timedelta(minutes=5),
    )

    parity = compare_feature_rows(offline, online)

    assert parity.passed
    assert parity.compared_fields == len(offline)
    assert replay_ids == ("evt-004",)


def test_rw0609_comparator_detects_feature_drift():
    offline = {
        "event_count": 4,
        "observable_value_mean": 2.5,
    }
    online = {
        "event_count": 4,
        "observable_value_mean": 2.6,
    }

    parity = compare_feature_rows(
        offline,
        online,
        tolerance=DEFAULT_FEATURE_TOLERANCE,
    )

    assert not parity.passed
    assert parity.compared_fields == 2
    assert "observable_value_mean" in parity.mismatches[0]


def test_rw0609_conflicting_replay_fails_before_parity():
    events = _fixture_events()
    conflicting = dict(events[0])
    conflicting["event_time"] = "2026-01-01T06:04:00Z"

    anchor = datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    compute_offline_features(
        events,
        partition_key=PARTITION,
        anchor_time=anchor,
        window_minutes=5,
    )

    with pytest.raises(ValueError, match="conflicting replay"):
        compute_online_features(
            [events[0], conflicting],
            partition_key=PARTITION,
            anchor_time=anchor,
            window_minutes=5,
            allowed_lateness=timedelta(minutes=5),
        )
