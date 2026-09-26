from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)
from config.ransomware.shared.validation.feature_leakage_guard import (
    validate_deployed_features,
)


WINDOW_MINUTES = (1, 5, 15)


EVIDENCE_DOMAINS: dict[str, frozenset[str]] = {
    "identity": frozenset(
        {
            "authentication_fan_out",
            "new_source_host",
            "privilege_transition",
            "account_novelty",
            "account_changes",
            "suspicious_account_activity",
            "authentication_novelty",
            "privilege_changes",
            "account_criticality",
            "authorization_records",
            "suspicious_admin_activity",
        }
    ),
    "endpoint": frozenset(
        {
            "new_source_host",
            "rare_process_chain",
            "process_chains",
            "process_parent_relationships",
            "host_novelty",
            "engineering_access",
        }
    ),
    "file": frozenset(
        {
            "file_write_spike",
            "file_rename_spike",
            "synthetic_extension_change",
            "entropy_proxy_increase",
            "file_write_rate",
            "file_evidence",
            "unusual_file_operations",
            "file_transfer_bursts",
            "project_file_access",
            "project_file_integrity",
            "configuration_file_activity",
            "configuration_package_access",
            "repository_history",
            "repository_integrity",
        }
    ),
    "network": frozenset(
        {
            "remote_connections",
            "remote_session_fan_out",
            "remote_sessions",
            "session_fan_out",
            "communications_health",
            "communications_evidence",
            "zone_crossings",
            "zone_transitions",
            "zone_path",
            "protected_zone_adjacency",
            "segmentation_status",
        }
    ),
    "backup": frozenset(
        {
            "backup_health",
            "backup_age",
            "job_failure_streak",
            "immutability_status",
            "restore_test_age",
            "backup_coverage",
            "backup_failures",
            "restore_test_results",
        }
    ),
    "service": frozenset(
        {
            "service_availability_decrease",
            "service_availability",
            "service_health",
            "service_state",
            "service_stops",
            "service_changes",
            "failover_state",
        }
    ),
    "asset": frozenset(
        {
            "host_novelty",
            "new_source_host",
            "dependency_criticality",
            "process_unit_criticality",
            "account_criticality",
        }
    ),
    "graph": frozenset(
        {
            "zone_crossings",
            "zone_transitions",
            "zone_path",
            "protected_zone_adjacency",
            "communications_health",
            "communications_evidence",
            "segmentation_status",
            "dependency_criticality",
            "service_dependencies",
        }
    ),
    "context": frozenset(
        {
            "vendor_schedule",
            "maintenance_window_metadata",
            "maintenance_approval",
            "campaign_metadata",
            "proof_test_schedule",
            "recovery_tier",
            "time_synchronization",
        }
    ),
    "quality": frozenset(
        {
            "ingestion_lag",
            "stale_point_rate",
            "log_termination",
            "missing_records",
            "stale_records",
            "batch_event_gaps",
            "cross_source_correlation",
            "database_health",
        }
    ),
}


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _window_events(
    events: list[ObservableScenarioEvent],
    end_time: datetime,
    duration_minutes: int,
) -> list[ObservableScenarioEvent]:
    start_time = end_time - timedelta(minutes=duration_minutes)

    return [
        event
        for event in events
        if start_time <= _parse_time(event.event_time) <= end_time
    ]


def _evidence_name(event: ObservableScenarioEvent) -> str:
    explicit_name = event.attributes.get("evidence_name")

    if isinstance(explicit_name, str) and explicit_name:
        return explicit_name

    return event.event_type


def _family_count(
    events: Iterable[ObservableScenarioEvent],
    families: frozenset[str],
) -> int:
    return sum(
        1
        for event in events
        if event.event_family in families
    )


def _domain_count(
    events: Iterable[ObservableScenarioEvent],
    domain: str,
) -> int:
    evidence_names = EVIDENCE_DOMAINS[domain]

    return sum(
        1
        for event in events
        if _evidence_name(event) in evidence_names
    )


def _unique_assets(
    events: Iterable[ObservableScenarioEvent],
) -> int:
    return len(
        {
            event.asset_id
            for event in events
        }
    )


def _unique_event_types(
    events: Iterable[ObservableScenarioEvent],
) -> int:
    return len(
        {
            _evidence_name(event)
            for event in events
        }
    )


def _observable_values(
    events: Iterable[ObservableScenarioEvent],
) -> list[float]:
    values: list[float] = []

    for event in events:
        for key in (
            "observable_value",
            "value",
            "activity_intensity",
            "degradation_severity",
        ):
            value = event.attributes.get(key)

            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                values.append(float(value))
                break

    return values


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        6,
    )


def _maximum(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(
        max(values),
        6,
    )


def _count_true_attribute(
    events: Iterable[ObservableScenarioEvent],
    attribute_name: str,
) -> int:
    return sum(
        1
        for event in events
        if event.attributes.get(attribute_name) is True
    )


def _distinct_attribute_values(
    events: Iterable[ObservableScenarioEvent],
    attribute_name: str,
) -> int:
    values = {
        value
        for event in events
        if (value := event.attributes.get(attribute_name)) is not None
    }

    return len(values)


def _numeric_attribute_sum(
    events: Iterable[ObservableScenarioEvent],
    attribute_name: str,
) -> float:
    total = 0.0

    for event in events:
        value = event.attributes.get(attribute_name)

        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            total += float(value)

    return round(total, 6)


def _numeric_attribute_mean(
    events: Iterable[ObservableScenarioEvent],
    attribute_name: str,
) -> float:
    values: list[float] = []

    for event in events:
        value = event.attributes.get(attribute_name)

        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            values.append(float(value))

    return _mean(values)


def _ratio(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        numerator / denominator,
        6,
    )


def extract_window_features(
    events: list[ObservableScenarioEvent],
    end_time: datetime,
    duration_minutes: int,
) -> dict[str, float | int]:
    """Extract observable-only features for one sliding window."""

    if duration_minutes not in WINDOW_MINUTES:
        raise ValueError(
            f"Unsupported feature window: {duration_minutes} minutes"
        )

    window = _window_events(
        events,
        end_time,
        duration_minutes,
    )

    values = _observable_values(window)

    # RW-060-2 identity features.
    auth_failure_count = _count_true_attribute(
        window,
        "auth_failure",
    )

    distinct_source_host_count = _distinct_attribute_values(
        window,
        "source_host",
    )

    new_source_relationship_count = _count_true_attribute(
        window,
        "new_source_relationship",
    )

    privilege_change_count = _count_true_attribute(
        window,
        "privilege_change",
    )

    # RW-060-3 endpoint/file features.
    rare_process_chain_count = _count_true_attribute(
        window,
        "rare_process_chain",
    )

    unsigned_process_count = _count_true_attribute(
        window,
        "unsigned_process",
    )

    task_service_creation_count = _count_true_attribute(
        window,
        "task_service_created",
    )

    write_count = _numeric_attribute_sum(
        window,
        "write_count",
    )

    rename_count = _numeric_attribute_sum(
        window,
        "rename_count",
    )

    extension_change_count = _numeric_attribute_sum(
        window,
        "extension_change_count",
    )

    file_event_count = _numeric_attribute_sum(
        window,
        "file_event_count",
    )

    entropy_proxy = _numeric_attribute_mean(
        window,
        "entropy_proxy",
    )

    features: dict[str, float | int] = {
        "window_duration_minutes": duration_minutes,
        "event_count": len(window),
        "unique_asset_count": _unique_assets(window),
        "unique_evidence_type_count": _unique_event_types(window),

        "identity_evidence_count": _domain_count(
            window,
            "identity",
        ),
        "auth_failure_count": auth_failure_count,
        "distinct_source_host_count": distinct_source_host_count,
        "new_source_relationship_count": new_source_relationship_count,
        "privilege_change_count": privilege_change_count,

        "endpoint_evidence_count": _domain_count(
            window,
            "endpoint",
        ),
        "file_evidence_count": _domain_count(
            window,
            "file",
        ),

        "rare_process_chain_score": _ratio(
            rare_process_chain_count,
            len(window),
        ),
        "unsigned_burst_count": unsigned_process_count,
        "task_service_creation_count": task_service_creation_count,
        "write_rate": round(
            write_count / duration_minutes,
            6,
        ),
        "rename_rate": round(
            rename_count / duration_minutes,
            6,
        ),
        "extension_change_ratio": _ratio(
            extension_change_count,
            file_event_count,
        ),
        "entropy_proxy": entropy_proxy,

        "network_evidence_count": _domain_count(
            window,
            "network",
        ),
        "backup_evidence_count": _domain_count(
            window,
            "backup",
        ),
        "service_evidence_count": _domain_count(
            window,
            "service",
        ),
        "asset_evidence_count": _domain_count(
            window,
            "asset",
        ),
        "graph_evidence_count": _domain_count(
            window,
            "graph",
        ),
        "context_evidence_count": _domain_count(
            window,
            "context",
        ),
        "quality_evidence_count": _domain_count(
            window,
            "quality",
        ),

        "observable_value_mean": _mean(values),
        "observable_value_max": _maximum(values),
    }

    validate_deployed_features(
        list(features)
    )

    return features


def extract_window_feature_series(
    events: list[ObservableScenarioEvent],
) -> list[dict[str, float | int | str]]:
    """Create 1-, 5- and 15-minute sliding-window feature rows."""

    if not events:
        return []

    ordered_events = sorted(
        events,
        key=lambda event: _parse_time(event.event_time),
    )

    rows: list[dict[str, float | int | str]] = []

    for end_time in (
        _parse_time(event.event_time)
        for event in ordered_events
    ):
        for duration_minutes in WINDOW_MINUTES:
            features = extract_window_features(
                ordered_events,
                end_time,
                duration_minutes,
            )

            rows.append(
                {
                    "window_end_time": end_time.isoformat(),
                    **features,
                }
            )

    return rows