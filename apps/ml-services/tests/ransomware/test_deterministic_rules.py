import pytest

from config.ransomware.rules.deterministic_rules import (
    RULES,
    RULESET_VERSION,
    evaluate_rule,
    evaluate_rules,
)


def _base_features():
    return {
        "privilege_change_count": 0,
        "auth_failure_count": 0,
        "new_source_relationship_count": 0,
        "distinct_source_host_count": 0,
        "zone_crossing_count": 0,
        "remote_admin_peer_count": 0,
        "new_peer_ratio": 0.0,
        "backup_evidence_count": 0,
        "backup_failure_streak": 0,
        "backup_age_minutes": 0,
        "restore_test_age_days": 0,
        "protected_boundary_hops": 0,
        "critical_service_exposure_count": 0,
        "service_evidence_count": 0,
        "service_availability_ratio": 1.0,
        "maintenance_approval_ratio": 0.0,
    }


def test_rw0701_ruleset_contains_six_versioned_rules():
    assert len(RULES) == 6
    assert all(rule.version == RULESET_VERSION == "1.0" for rule in RULES)
    assert [
        rule.rule_id for rule in RULES
    ] == [
        "RW-070-R01",
        "RW-070-R02",
        "RW-070-R03",
        "RW-070-R04",
        "RW-070-R05",
        "RW-070-R06",
    ]


@pytest.mark.parametrize(
    ("rule_id", "updates"),
    [
        (
            "RW-070-R01",
            {
                "privilege_change_count": 1,
                "auth_failure_count": 2,
            },
        ),
        (
            "RW-070-R02",
            {
                "zone_crossing_count": 1,
                "remote_admin_peer_count": 1,
            },
        ),
        (
            "RW-070-R03",
            {
                "backup_evidence_count": 1,
                "backup_failure_streak": 2,
            },
        ),
        (
            "RW-070-R04",
            {
                "protected_boundary_hops": 1,
            },
        ),
        (
            "RW-070-R05",
            {
                "service_evidence_count": 1,
                "service_availability_ratio": 0.0,
            },
        ),
        (
            "RW-070-R06",
            {
                "maintenance_approval_ratio": 1.0,
                "privilege_change_count": 1,
            },
        ),
    ],
)
def test_rw0701_each_rule_triggers_on_predeclared_evidence(
    rule_id,
    updates,
):
    features = _base_features()
    features.update(updates)

    result = evaluate_rule(rule_id, features)

    assert result.triggered is True
    assert result.evidence_count >= 1
    assert result.version == "1.0"
    assert result.rule_id == rule_id
    assert result.explanation


def test_rw0701_rules_do_not_trigger_on_empty_evidence():
    results = evaluate_rules(_base_features())

    assert len(results) == 6
    assert all(result.triggered is False for result in results)
    assert all(
        isinstance(result.explanation, str)
        and result.explanation.strip()
        for result in results
    )


def test_rw0701_rule_outputs_are_deterministic():
    features = _base_features()
    features.update(
        {
            "privilege_change_count": 1,
            "auth_failure_count": 2,
            "zone_crossing_count": 1,
        }
    )

    first = evaluate_rules(features)
    second = evaluate_rules(features)

    assert first == second


def test_rw0701_missing_input_is_rejected():
    features = _base_features()
    del features["privilege_change_count"]

    with pytest.raises(
        ValueError,
        match="missing required features",
    ):
        evaluate_rule("RW-070-R01", features)


def test_rw0701_unknown_rule_is_rejected():
    with pytest.raises(
        ValueError,
        match="unknown rule_id",
    ):
        evaluate_rule("RW-070-R99", _base_features())
