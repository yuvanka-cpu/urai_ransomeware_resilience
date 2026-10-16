from __future__ import annotations

from dataclasses import replace
import random

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


def _rng(event: ObservableScenarioEvent) -> random.Random:
    seed = (
        int(event.scenario_seed) * 1_000_003
        + int(event.sequence_index) * 9_176
    )
    return random.Random(seed)


def _clip(value: float, low: float, high: float) -> float:
    return round(max(low, min(high, value)), 6)


def enrich_cycle2_events(
    events: list[ObservableScenarioEvent],
) -> list[ObservableScenarioEvent]:
    """
    Add concrete observable telemetry attributes required by the 54-feature
    Cycle-2 contract.

    This function uses only observable event family/type and existing
    observable attributes. It does not read scenario labels or truth fields.
    """
    enriched: list[ObservableScenarioEvent] = []

    for event in events:
        attrs = dict(event.attributes)
        event_type = str(event.event_type).lower()
        event_family = str(event.event_family).lower()
        rng = _rng(event)

        # Identity / authentication.
        if event_family in {"authentication", "identity", "account"}:
            attrs.setdefault(
                "source_host",
                f"src-{rng.randint(1, 6)}",
            )

        if event_type in {
            "authentication_novelty",
            "new_source_host",
            "account_novelty",
        }:
            attrs["new_source_relationship"] = True

        if event_type in {
            "authentication_fan_out",
            "authentication_novelty",
        }:
            attrs["auth_failure"] = rng.random() < 0.30

        # Privilege / authorization.
        if event_type in {
            "privilege_changes",
            "privilege_transition",
        }:
            attrs["privilege_change"] = True

        # Endpoint / process evidence.
        if event_type == "rare_process_chain":
            attrs["rare_process_chain"] = True

        if event_type in {
            "process_chains",
            "process_parent_relationships",
        }:
            attrs.setdefault(
                "rare_process_chain",
                rng.random() < 0.15,
            )

        if event_type in {
            "engineering_access",
            "suspicious_admin_activity",
        }:
            attrs.setdefault("task_service_created", False)

        # Criticality / recovery context.
        if "criticality" in event_type:
            attrs["criticality_score"] = _clip(
                rng.uniform(0.65, 1.0),
                0.0,
                1.0,
            )

        if event_type == "recovery_tier":
            attrs["recovery_tier"] = rng.randint(1, 3)

        if event_type == "protected_zone_adjacency":
            attrs["protected_boundary_hops"] = rng.randint(1, 3)
            attrs["critical_service_exposure"] = True

        if event_type in {
            "service_dependencies",
            "dependency_criticality",
        }:
            attrs.setdefault(
                "critical_service_exposure",
                rng.random() < 0.55,
            )

        # Network / remote activity.
        if event_type in {
            "remote_connections",
            "remote_sessions",
            "remote_session_fan_out",
        }:
            attrs["remote_admin_peer_count"] = rng.randint(1, 4)
            attrs["new_peer_count"] = (
                rng.randint(0, 2)
                if event_type != "remote_sessions"
                else rng.randint(0, 1)
            )

        if event_type in {
            "file_transfer_bursts",
            "network_baseline",
        }:
            attrs.setdefault(
                "outbound_bytes",
                rng.randint(10_000, 100_000),
            )

        if event_type == "zone_crossings":
            attrs["zone_crossing"] = True

        # File activity baseline.
        if event_family == "file":
            attrs.setdefault(
                "file_event_count",
                rng.randint(1, 3),
            )
            attrs.setdefault(
                "write_count",
                rng.randint(1, 8),
            )
            attrs.setdefault(
                "rename_count",
                0,
            )
            attrs.setdefault(
                "extension_change_count",
                0,
            )
            attrs.setdefault(
                "entropy_proxy",
                rng.uniform(0.20, 0.55),
            )

        if event_type == "unusual_file_operations":
            attrs["file_event_count"] = rng.randint(3, 7)
            attrs["write_count"] = rng.randint(5, 15)
            attrs["entropy_proxy"] = rng.uniform(0.45, 0.75)

        # Synthetic attack-effect observables.
        attack_stage_strength = {
            "initial_access_observable": 0.45,
            "discovery_observable": 0.50,
            "execution_persistence_observable": 0.60,
            "privilege_escalation_observable": 0.68,
            "lateral_movement_observable": 0.74,
            "staging_observable": 0.80,
            "encryption_impact_observable": 0.92,
            "extortion_marker_observable": 0.88,
            "recovery_impairment_observable": 0.84,
            "recovery_observable": 0.40,
        }

        if event_type in attack_stage_strength:
            attrs["stage_transition_score"] = _clip(
                attack_stage_strength[event_type]
                + rng.uniform(-0.06, 0.06),
                0.0,
                1.0,
            )

        if event_type == "encryption_impact_observable":
            attrs["file_event_count"] = rng.randint(10, 20)
            attrs["write_count"] = rng.randint(12, 30)
            attrs["rename_count"] = rng.randint(5, 14)
            attrs["extension_change_count"] = rng.randint(4, 12)
            attrs["entropy_proxy"] = rng.uniform(0.84, 0.99)
            attrs["service_available"] = False

        if event_type == "recovery_impairment_observable":
            attrs["backup_failure_streak"] = rng.randint(2, 4)
            attrs["backup_age_minutes"] = rng.randint(240, 720)
            attrs["immutable_copy"] = False
            attrs["service_available"] = False

        # Benign lookalikes.
        if event_family == "benign_activity":
            authorized = bool(attrs.get("authorized", False))
            attrs["maintenance_approved"] = authorized

            if event_type == "bulk_copy":
                attrs["file_event_count"] = rng.randint(8, 18)
                attrs["write_count"] = rng.randint(8, 20)
                attrs["rename_count"] = 0
                attrs["extension_change_count"] = 0
                attrs["entropy_proxy"] = rng.uniform(0.25, 0.55)

            elif event_type == "compression":
                attrs["file_event_count"] = rng.randint(4, 10)
                attrs["write_count"] = rng.randint(4, 12)
                attrs["entropy_proxy"] = rng.uniform(0.55, 0.75)

            elif event_type in {
                "patching",
                "deployment",
                "relay_configuration_work",
                "turnaround_work",
            }:
                attrs["write_count"] = rng.randint(3, 10)
                attrs["task_service_created"] = (
                    event_type == "deployment"
                )

            elif event_type in {
                "approved_administration",
                "vendor_support",
            }:
                attrs["remote_admin_peer_count"] = rng.randint(1, 3)
                attrs["new_peer_count"] = 0

            elif event_type == "backup":
                attrs["backup_age_minutes"] = rng.randint(15, 120)
                attrs["backup_failure_streak"] = 0
                attrs["immutable_copy"] = True

            elif event_type == "restore_test":
                attrs["restore_test_age_days"] = rng.randint(1, 30)
                attrs["immutable_copy"] = True

            elif event_type in {
                "campaign_changes",
                "historian_replay",
                "failover",
            }:
                attrs["stage_transition_score"] = rng.uniform(
                    0.15,
                    0.35,
                )

        # Backup / restore observables.
        if event_type == "backup_age":
            attrs["backup_age_minutes"] = rng.randint(15, 360)

        if event_type == "backup_failures":
            attrs["backup_failure_streak"] = rng.randint(0, 3)

        if event_type == "backup_coverage":
            attrs.setdefault("immutable_copy", rng.random() < 0.8)

        if event_type == "immutability_status":
            attrs["immutable_copy"] = True

        if event_type == "restore_test_age":
            attrs["restore_test_age_days"] = rng.randint(1, 45)

        # Service health.
        if event_type in {
            "service_availability",
            "service_health",
            "service_state",
        }:
            attrs["service_available"] = True

        if event_type == "service_stops":
            attrs["service_available"] = False

        if event_type == "service_availability_decrease":
            attrs["service_available"] = False

        # Maintenance.
        if event_type == "maintenance_approval":
            attrs["maintenance_approved"] = True

        # Data-quality / telemetry faults.
        quality_map = {
            "host_outage": {
                "service_available": False,
                "missing_source": True,
            },
            "network_interruption": {
                "missing_source": True,
                "late_event": True,
            },
            "disk_pressure": {
                "ingestion_lag_seconds": rng.randint(30, 180),
                "stale_data": True,
            },
            "backup_failure": {
                "backup_failure_streak": rng.randint(2, 4),
            },
            "source_loss": {
                "missing_source": True,
            },
            "reordered_late_events": {
                "late_event": True,
                "ingestion_lag_seconds": rng.randint(20, 240),
            },
            "partial_evidence": {
                "missing_source": True,
                "late_event": rng.random() < 0.5,
            },
        }

        if event_family == "telemetry_quality":
            for key, value in quality_map.get(event_type, {}).items():
                attrs[key] = value

        # Generic data-quality evidence.
        if event_type == "ingestion_lag":
            attrs["ingestion_lag_seconds"] = rng.randint(1, 120)

        if event_type in {"stale_point_rate", "stale_records"}:
            attrs["stale_data"] = True

        if event_type == "missing_records":
            attrs["missing_source"] = True

        # Cross-source / zone events do not fabricate a stage-transition
        # score. Progression evidence must come from explicit observable
        # transition events or explicitly supplied observable attributes.
        enriched.append(
            replace(event, attributes=attrs)
        )

    return enriched
