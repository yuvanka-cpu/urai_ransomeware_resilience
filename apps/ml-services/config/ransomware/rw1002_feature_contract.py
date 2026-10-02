"""RW-100-2 runtime feature-schema and leakage validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


EXPECTED_FEATURES = frozenset(
    {
        "alarm_support_health_ratio",
        "asset_evidence_count",
        "auth_failure_count",
        "backup_age_minutes",
        "backup_evidence_count",
        "backup_failure_streak",
        "batch_quality_dependency_exposure_count",
        "communications_health_ratio",
        "context_evidence_count",
        "critical_service_exposure_count",
        "criticality_score",
        "dcs_support_exposure_count",
        "distinct_source_host_count",
        "endpoint_evidence_count",
        "entropy_proxy",
        "event_count",
        "extension_change_ratio",
        "file_evidence_count",
        "graph_evidence_count",
        "identity_evidence_count",
        "immutable_copy_present_count",
        "ingestion_lag_seconds",
        "late_event_ratio",
        "maintenance_approval_ratio",
        "missing_source_mask",
        "network_evidence_count",
        "new_peer_ratio",
        "new_source_relationship_count",
        "observable_value_max",
        "observable_value_mean",
        "outbound_bytes",
        "privilege_change_count",
        "protected_boundary_hops",
        "quality_evidence_count",
        "rare_process_chain_score",
        "recovery_tier",
        "relay_management_adjacency_count",
        "remote_admin_peer_count",
        "rename_rate",
        "restore_test_age_days",
        "scada_visibility_ratio",
        "service_availability_ratio",
        "service_evidence_count",
        "sis_esd_adjacency_count",
        "stage_transition_score",
        "stale_data_ratio",
        "substation_support_exposure_count",
        "task_service_creation_count",
        "unique_asset_count",
        "unique_evidence_type_count",
        "unsigned_burst_count",
        "window_duration_minutes",
        "write_rate",
        "zone_crossing_count",
    }
)

FORBIDDEN_FEATURES = frozenset(
    {
        "scenario_id",
        "scenario_seed",
        "is_ransomware",
        "incident_stage_truth",
        "affected_asset_truth",
        "blast_radius_truth",
        "analyst_disposition",
    }
)

EXPECTED_FEATURE_COUNT = 54


@dataclass(frozen=True)
class FeatureContractValidation:
    valid: bool
    feature_count: int
    missing_features: tuple[str, ...]
    unexpected_features: tuple[str, ...]
    forbidden_features: tuple[str, ...]
    duplicate_features: tuple[str, ...]


class FeatureContractError(ValueError):
    """Raised when runtime features violate the frozen feature contract."""


def _duplicate_names(feature_names: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for name in feature_names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)

    return tuple(sorted(duplicates))


def validate_feature_names(
    feature_names: Iterable[str],
) -> FeatureContractValidation:
    names = tuple(feature_names)

    duplicates = _duplicate_names(names)
    actual = set(names)

    missing = tuple(sorted(EXPECTED_FEATURES - actual))
    unexpected = tuple(sorted(actual - EXPECTED_FEATURES))
    forbidden = tuple(sorted(actual & FORBIDDEN_FEATURES))

    result = FeatureContractValidation(
        valid=not any(
            (
                missing,
                unexpected,
                forbidden,
                duplicates,
                len(names) != EXPECTED_FEATURE_COUNT,
            )
        ),
        feature_count=len(names),
        missing_features=missing,
        unexpected_features=unexpected,
        forbidden_features=forbidden,
        duplicate_features=duplicates,
    )

    if not result.valid:
        problems: list[str] = []

        if missing:
            problems.append(f"missing={list(missing)}")
        if unexpected:
            problems.append(f"unexpected={list(unexpected)}")
        if forbidden:
            problems.append(f"forbidden={list(forbidden)}")
        if duplicates:
            problems.append(f"duplicates={list(duplicates)}")
        if len(names) != EXPECTED_FEATURE_COUNT:
            problems.append(
                f"count={len(names)}, expected={EXPECTED_FEATURE_COUNT}"
            )

        raise FeatureContractError(
            "runtime feature contract violation: " + "; ".join(problems)
        )

    return result


def validate_feature_row(
    row: Mapping[str, object],
) -> FeatureContractValidation:
    """Validate feature keys without altering or silently dropping fields."""
    return validate_feature_names(row.keys())


def main() -> None:
    result = validate_feature_names(sorted(EXPECTED_FEATURES))

    print("=== RW-100-2 FEATURE CONTRACT ===")
    print("Expected features:", EXPECTED_FEATURE_COUNT)
    print("Validated features:", result.feature_count)
    print("Forbidden fields:", len(FORBIDDEN_FEATURES))
    print("Missing:", len(result.missing_features))
    print("Unexpected:", len(result.unexpected_features))
    print("Duplicates:", len(result.duplicate_features))
    print("Status: valid")


if __name__ == "__main__":
    main()
