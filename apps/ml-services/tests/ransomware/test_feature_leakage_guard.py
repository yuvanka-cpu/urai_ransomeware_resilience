import pytest

from config.ransomware.shared.validation.feature_leakage_guard import (
    FORBIDDEN_DEPLOYED_FEATURES,
    validate_deployed_features,
)


def test_allowed_observable_features_pass():
    validate_deployed_features(
        [
            "event_time",
            "event_family",
            "event_type",
            "asset_id",
            "severity",
            "network_connection_count",
            "process_activity_count",
        ]
    )


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_DEPLOYED_FEATURES))
def test_forbidden_truth_fields_are_rejected(forbidden):
    with pytest.raises(ValueError, match="RW-050-5 feature leakage detected"):
        validate_deployed_features(["event_type", forbidden])


def test_forbidden_check_is_case_insensitive():
    with pytest.raises(ValueError, match="RW-050-5 feature leakage detected"):
        validate_deployed_features(["EVENT_TYPE", "SCENARIO_ID"])


def test_multiple_forbidden_fields_are_rejected():
    with pytest.raises(ValueError, match="RW-050-5 feature leakage detected"):
        validate_deployed_features(
            [
                "event_type",
                "scenario_id",
                "scenario_seed",
                "incident_stage_truth",
            ]
        )
