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

    with pytest.raises(ValueError, match="Unsupported feature window"):
        extract_window_features(
            events,
            end_time,
            10,
        )


def test_rw0601_does_not_emit_ground_truth_features() -> None:
    events = [
        _event(
            0,
            "file",
            "file_write_spike",
            attributes={
                "value": 0.8,
                "is_ransomware": True,
                "incident_stage_truth": "encryption_impact",
            },
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

    features = extract_window_features(
        events,
        end_time,
        1,
    )

    forbidden = {
        "scenario_id",
        "scenario_seed",
        "is_ransomware",
        "incident_stage_truth",
        "affected_asset_truth",
        "blast_radius_truth",
        "analyst_disposition",
    }

    assert not forbidden.intersection(features)
def test_rw0602_identity_features_manual_one_minute_window() -> None:
    events = [
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-a",
            },
        ),
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-b",
            },
        ),
        _event(
            0,
            "identity",
            "new_source_relationship",
            attributes={
                "new_source_relationship": True,
                "source_host": "host-c",
            },
        ),
        _event(
            0,
            "identity",
            "privilege_change",
            attributes={
                "privilege_change": True,
                "source_host": "host-a",
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
    assert features["distinct_source_host_count"] == 3
    assert features["new_source_relationship_count"] == 1
    assert features["privilege_change_count"] == 1


def test_rw0602_identity_features_respect_five_minute_boundary() -> None:
    events = [
        _event(
            0,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-a",
            },
        ),
        _event(
            1,
            "identity",
            "authentication_failure",
            attributes={
                "auth_failure": True,
                "source_host": "host-b",
            },
        ),
        _event(
            5,
            "identity",
            "privilege_change",
            attributes={
                "privilege_change": True,
                "source_host": "host-c",
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

    # [06:00, 06:05] is inclusive.
    assert features["auth_failure_count"] == 2
    assert features["distinct_source_host_count"] == 3
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
            },
        ),
        _event(
            1,
            "identity",
            "privilege_change",
            attributes={
                "privilege_change": True,
                "source_host": "host-b",
            },
        ),
        _event(
            5,
            "identity",
            "new_source_relationship",
            attributes={
                "new_source_relationship": True,
                "source_host": "host-c",
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

    # Only event at 06:05 belongs to [06:04, 06:05].
    assert features["auth_failure_count"] == 0
    assert features["distinct_source_host_count"] == 1
    assert features["new_source_relationship_count"] == 1
    assert features["privilege_change_count"] == 0
