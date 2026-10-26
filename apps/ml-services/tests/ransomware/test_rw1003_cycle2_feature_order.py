import math

from config.ransomware.rw1002_feature_contract import EXPECTED_FEATURES
from config.ransomware.rw1003_canonical_inference_cycle2 import (
    _build_catboost_features,
    canonical_inference,
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


def test_cycle2_canonical_inference_smoke_and_safety_contract():
    """Exercise rw0906_v2 inference with synthetic input only."""

    features = {name: 0.0 for name in EXPECTED_FEATURES}

    result = canonical_inference(
        observable_features=features,
        industry="energy",
        site_types="refinery",
        rule_score=0.1,
        anomaly_score=0.2,
        graph_score=0.15,
        sector="energy",
    )

    assert result["bundle_version"] == "rw0906_v2"
    assert result["task"] == "RW-100-3"
    assert result["sector"] == "energy"
    assert result["decision"] in {"normal", "investigate", "high_risk"}

    for probability in result["probabilities"].values():
        assert math.isfinite(probability)
        assert 0.0 <= probability <= 1.0

    assert result["components"]["temporal_score"] is None
    assert result["components"]["temporal_missing"] == 1

    contract = result["runtime_contract"]
    assert contract["synthetic_only"] is True
    assert contract["human_approval_required"] is True
    assert contract["real_action_executed"] is False
    assert contract["operational_state_claimed"] is False
    assert contract["physical_safety_determination"] == "not_determined"