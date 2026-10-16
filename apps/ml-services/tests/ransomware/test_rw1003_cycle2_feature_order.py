from config.ransomware.rw1002_feature_contract import EXPECTED_FEATURES
from config.ransomware.rw1003_canonical_inference_cycle2 import (
    _build_catboost_features,
)


def test_cycle2_catboost_feature_order_matches_training_contract():
    """Cycle 2 CatBoost inference must use sorted training feature order."""

    features = {
        name: index
        for index, name in enumerate(sorted(EXPECTED_FEATURES))
    }

    industry = "energy"
    site_types = "refinery"

    actual = _build_catboost_features(
        observable_features=features,
        industry=industry,
        site_types=site_types,
    )

    expected = [
        features[name]
        for name in sorted(EXPECTED_FEATURES)
    ] + [industry, site_types]

    assert len(actual) == 56
    assert actual == expected
