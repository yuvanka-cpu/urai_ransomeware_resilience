from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping


RULESET_VERSION = "1.0"

FeatureMap = Mapping[str, float | int]
RuleEvaluator = Callable[[FeatureMap], tuple[bool, int, str]]


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    version: str
    name: str
    description: str
    inputs: tuple[str, ...]
    evaluator: RuleEvaluator


@dataclass(frozen=True)
class RuleEvidence:
    rule_id: str
    version: str
    triggered: bool
    evidence_count: int
    explanation: str
    inputs: tuple[str, ...]


def _unusual_privileged_access(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    privilege_change = features["privilege_change_count"] >= 1
    auth_failures = features["auth_failure_count"] >= 2
    new_relationship = features["new_source_relationship_count"] >= 1
    distinct_hosts = features["distinct_source_host_count"] >= 2

    support_count = sum(
        (auth_failures, new_relationship, distinct_hosts)
    )
    triggered = privilege_change and support_count >= 1

    explanation = (
        "Privilege-change evidence co-occurs with "
        "unusual authentication/source evidence."
        if triggered
        else "Required privileged-access evidence combination not observed."
    )

    return triggered, int(privilege_change) + support_count, explanation


def _cross_zone_movement(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    zone_crossing = features["zone_crossing_count"] >= 1
    remote_peer = features["remote_admin_peer_count"] >= 1
    new_peer = features["new_peer_ratio"] > 0.0

    support_count = int(remote_peer) + int(new_peer)
    triggered = zone_crossing and support_count >= 1

    explanation = (
        "Zone-crossing evidence co-occurs with remote-administration "
        "or new-peer evidence."
        if triggered
        else "Required cross-zone movement evidence combination not observed."
    )

    return triggered, int(zone_crossing) + support_count, explanation


def _recovery_impairment(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    has_backup_evidence = features["backup_evidence_count"] >= 1
    failure_streak = features["backup_failure_streak"] >= 2
    old_backup = features["backup_age_minutes"] >= 60
    old_restore_test = features["restore_test_age_days"] >= 30

    impairment_count = sum(
        (failure_streak, old_backup, old_restore_test)
    )
    triggered = has_backup_evidence and impairment_count >= 1

    explanation = (
        "Observable backup/recovery evidence indicates at least one "
        "predeclared recovery-impairment condition."
        if triggered
        else "No predeclared recovery-impairment condition observed."
    )

    return triggered, int(has_backup_evidence) + impairment_count, explanation


def _protected_boundary_adjacency(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    boundary_hops = features["protected_boundary_hops"] >= 1
    critical_service = features["critical_service_exposure_count"] >= 1

    evidence_count = int(boundary_hops) + int(critical_service)
    triggered = evidence_count >= 1

    explanation = (
        "Observable protected-boundary or critical-service exposure "
        "evidence is present."
        if triggered
        else "No protected-boundary adjacency evidence observed."
    )

    return triggered, evidence_count, explanation


def _service_loss(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    has_service_evidence = features["service_evidence_count"] >= 1
    degraded = features["service_availability_ratio"] < 1.0

    evidence_count = int(has_service_evidence) + int(degraded)
    triggered = has_service_evidence and degraded

    explanation = (
        "Observable service evidence indicates less than complete "
        "service availability."
        if triggered
        else "Complete observable service availability or no service evidence."
    )

    return triggered, evidence_count, explanation


def _maintenance_authorization_contradiction(
    features: FeatureMap,
) -> tuple[bool, int, str]:
    maintenance = features["maintenance_approval_ratio"] > 0.0
    privilege_change = features["privilege_change_count"] >= 1
    zone_crossing = features["zone_crossing_count"] >= 1
    boundary_hops = features["protected_boundary_hops"] >= 1
    new_relationship = features["new_source_relationship_count"] >= 1

    conflicting_evidence = sum(
        (
            privilege_change,
            zone_crossing,
            boundary_hops,
            new_relationship,
        )
    )
    triggered = maintenance and conflicting_evidence >= 1

    explanation = (
        "Approved-maintenance evidence co-occurs with unusual "
        "privileged, relationship, zone or protected-boundary evidence; "
        "review is required."
        if triggered
        else "No predeclared maintenance-authorization contradiction observed."
    )

    return (
        triggered,
        int(maintenance) + conflicting_evidence,
        explanation,
    )


RULES: tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="RW-070-R01",
        version=RULESET_VERSION,
        name="unusual_privileged_access",
        description=(
            "Identifies observable privilege changes accompanied by "
            "unusual authentication or source-relationship evidence."
        ),
        inputs=(
            "privilege_change_count",
            "auth_failure_count",
            "new_source_relationship_count",
            "distinct_source_host_count",
        ),
        evaluator=_unusual_privileged_access,
    ),
    RuleDefinition(
        rule_id="RW-070-R02",
        version=RULESET_VERSION,
        name="cross_zone_movement",
        description=(
            "Identifies observable zone crossings accompanied by "
            "remote-administration or new-peer evidence."
        ),
        inputs=(
            "zone_crossing_count",
            "remote_admin_peer_count",
            "new_peer_ratio",
        ),
        evaluator=_cross_zone_movement,
    ),
    RuleDefinition(
        rule_id="RW-070-R03",
        version=RULESET_VERSION,
        name="recovery_impairment",
        description=(
            "Identifies observable backup/recovery conditions using "
            "backup failure streak, backup age or restore-test age."
        ),
        inputs=(
            "backup_evidence_count",
            "backup_failure_streak",
            "backup_age_minutes",
            "restore_test_age_days",
        ),
        evaluator=_recovery_impairment,
    ),
    RuleDefinition(
        rule_id="RW-070-R04",
        version=RULESET_VERSION,
        name="protected_boundary_adjacency",
        description=(
            "Identifies observable protected-boundary hops or "
            "critical-service exposure."
        ),
        inputs=(
            "protected_boundary_hops",
            "critical_service_exposure_count",
        ),
        evaluator=_protected_boundary_adjacency,
    ),
    RuleDefinition(
        rule_id="RW-070-R05",
        version=RULESET_VERSION,
        name="service_loss",
        description=(
            "Identifies observable service evidence with incomplete "
            "service availability."
        ),
        inputs=(
            "service_evidence_count",
            "service_availability_ratio",
        ),
        evaluator=_service_loss,
    ),
    RuleDefinition(
        rule_id="RW-070-R06",
        version=RULESET_VERSION,
        name="maintenance_authorization_contradiction",
        description=(
            "Identifies approved-maintenance evidence co-occurring with "
            "unusual privilege, relationship, zone or boundary evidence."
        ),
        inputs=(
            "maintenance_approval_ratio",
            "privilege_change_count",
            "zone_crossing_count",
            "protected_boundary_hops",
            "new_source_relationship_count",
        ),
        evaluator=_maintenance_authorization_contradiction,
    ),
)


_RULE_INDEX = {rule.rule_id: rule for rule in RULES}


def evaluate_rule(
    rule_id: str,
    features: FeatureMap,
) -> RuleEvidence:
    try:
        rule = _RULE_INDEX[rule_id]
    except KeyError as exc:
        raise ValueError(f"unknown rule_id: {rule_id}") from exc

    missing = [
        field
        for field in rule.inputs
        if field not in features
    ]

    if missing:
        raise ValueError(
            f"{rule_id}: missing required features: "
            + ", ".join(missing)
        )

    triggered, evidence_count, explanation = rule.evaluator(features)

    return RuleEvidence(
        rule_id=rule.rule_id,
        version=rule.version,
        triggered=triggered,
        evidence_count=evidence_count,
        explanation=explanation,
        inputs=rule.inputs,
    )


def evaluate_rules(
    features: FeatureMap,
) -> tuple[RuleEvidence, ...]:
    return tuple(
        evaluate_rule(rule.rule_id, features)
        for rule in RULES
    )
