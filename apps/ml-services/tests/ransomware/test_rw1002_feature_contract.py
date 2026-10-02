import pytest

from config.ransomware.rw1002_feature_contract import (
    EXPECTED_FEATURES,
    FeatureContractError,
    validate_feature_names,
)


def test_exact_frozen_contract_passes():
    result = validate_feature_names(sorted(EXPECTED_FEATURES))

    assert result.valid
    assert result.feature_count == 54
    assert result.missing_features == ()
    assert result.unexpected_features == ()
    assert result.forbidden_features == ()
    assert result.duplicate_features == ()


def test_missing_feature_fails():
    features = sorted(EXPECTED_FEATURES - {"event_count"})

    with pytest.raises(FeatureContractError, match="missing"):
        validate_feature_names(features)


def test_unexpected_feature_fails():
    features = sorted(EXPECTED_FEATURES) + ["invented_runtime_feature"]

    with pytest.raises(FeatureContractError, match="unexpected"):
        validate_feature_names(features)


def test_forbidden_truth_field_fails():
    features = sorted(EXPECTED_FEATURES) + ["is_ransomware"]

    with pytest.raises(FeatureContractError, match="forbidden"):
        validate_feature_names(features)


def test_duplicate_feature_fails():
    features = sorted(EXPECTED_FEATURES) + ["event_count"]

    with pytest.raises(FeatureContractError, match="duplicates"):
        validate_feature_names(features)
