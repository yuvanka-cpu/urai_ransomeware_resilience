import pytest

from config.ransomware.baselines import (
    RobustAnomalyBaseline,
)


FEATURES = (
    "auth_failure_count",
    "zone_crossing_count",
    "backup_failure_streak",
)


def _training_rows():
    return [
        {
            "auth_failure_count": 0,
            "zone_crossing_count": 0,
            "backup_failure_streak": 0,
        },
        {
            "auth_failure_count": 1,
            "zone_crossing_count": 0,
            "backup_failure_streak": 0,
        },
        {
            "auth_failure_count": 0,
            "zone_crossing_count": 1,
            "backup_failure_streak": 0,
        },
        {
            "auth_failure_count": 1,
            "zone_crossing_count": 1,
            "backup_failure_streak": 1,
        },
        {
            "auth_failure_count": 0,
            "zone_crossing_count": 0,
            "backup_failure_streak": 1,
        },
        {
            "auth_failure_count": 1,
            "zone_crossing_count": 0,
            "backup_failure_streak": 1,
        },
    ]


def test_rw0703_baseline_fits_and_scores():
    baseline = RobustAnomalyBaseline(FEATURES).fit(
        _training_rows()
    )

    result = baseline.score(
        {
            "auth_failure_count": 0,
            "zone_crossing_count": 0,
            "backup_failure_streak": 0,
        }
    )

    assert isinstance(result.univariate_evidence_count, int)
    assert result.multivariate_threshold > 0
    assert isinstance(result.isolation_score, float)
    assert result.explanation


def test_rw0703_univariate_threshold_detects_robust_outlier():
    baseline = RobustAnomalyBaseline(
        ("auth_failure_count",),
        z_threshold=3.5,
    ).fit(
        [
            {"auth_failure_count": 0},
            {"auth_failure_count": 1},
            {"auth_failure_count": 0},
            {"auth_failure_count": 1},
            {"auth_failure_count": 0},
            {"auth_failure_count": 1},
        ]
    )

    result = baseline.score(
        {"auth_failure_count": 100}
    )

    assert result.univariate_triggered is True
    assert result.univariate_evidence_count == 1


def test_rw0703_multivariate_threshold_is_explicit():
    baseline = RobustAnomalyBaseline(FEATURES)

    assert baseline.multivariate_threshold == pytest.approx(
        3.5 * (3 ** 0.5)
    )


def test_rw0703_isolation_forest_is_reproducible():
    rows = _training_rows()

    first = RobustAnomalyBaseline(
        FEATURES,
        random_state=42,
    ).fit(rows)

    second = RobustAnomalyBaseline(
        FEATURES,
        random_state=42,
    ).fit(rows)

    probe = {
        "auth_failure_count": 10,
        "zone_crossing_count": 8,
        "backup_failure_streak": 9,
    }

    assert first.score(probe) == second.score(probe)


def test_rw0703_no_anomaly_for_typical_row_from_training_distribution():
    baseline = RobustAnomalyBaseline(FEATURES).fit(
        _training_rows()
    )

    result = baseline.score(
        {
            "auth_failure_count": 1,
            "zone_crossing_count": 0,
            "backup_failure_streak": 1,
        }
    )

    assert result.univariate_triggered is False
    assert result.multivariate_triggered is False


def test_rw0703_missing_feature_is_rejected():
    baseline = RobustAnomalyBaseline(FEATURES).fit(
        _training_rows()
    )

    with pytest.raises(
        ValueError,
        match="missing required features",
    ):
        baseline.score(
            {
                "auth_failure_count": 1,
                "zone_crossing_count": 0,
            }
        )


def test_rw0703_empty_training_is_rejected():
    with pytest.raises(
        ValueError,
        match="at least two training rows",
    ):
        RobustAnomalyBaseline(FEATURES).fit([])


def test_rw0703_duplicate_feature_names_are_rejected():
    with pytest.raises(
        ValueError,
        match="feature_names must be unique",
    ):
        RobustAnomalyBaseline(
            ("auth_failure_count", "auth_failure_count")
        )


def test_rw0703_evidence_has_no_final_decision_fields():
    baseline = RobustAnomalyBaseline(FEATURES).fit(
        _training_rows()
    )

    result = baseline.score(
        {
            "auth_failure_count": 100,
            "zone_crossing_count": 50,
            "backup_failure_streak": 40,
        }
    )

    forbidden = {
        "decision",
        "severity",
        "confidence",
        "action",
        "recommended_action",
        "high_risk",
    }

    assert not forbidden.intersection(result.__dataclass_fields__)
    assert "final incident decision" in result.explanation


def test_rw0703_isolation_only_is_still_evidence():
    baseline = RobustAnomalyBaseline(
        FEATURES,
        z_threshold=1_000_000,
    ).fit(_training_rows())

    result = baseline.score(
        {
            "auth_failure_count": 100,
            "zone_crossing_count": 100,
            "backup_failure_streak": 100,
        }
    )

    assert result.isolation_triggered is True
    assert result.univariate_triggered is False
    assert result.explanation
    assert "evidence only" in result.explanation


def test_rw0703_scoring_is_deterministic_for_identical_input():
    baseline = RobustAnomalyBaseline(FEATURES).fit(
        _training_rows()
    )

    row = {
        "auth_failure_count": 2,
        "zone_crossing_count": 1,
        "backup_failure_streak": 2,
    }

    assert baseline.score(row) == baseline.score(row)
