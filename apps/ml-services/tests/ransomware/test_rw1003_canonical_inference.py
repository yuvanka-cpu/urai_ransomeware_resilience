from __future__ import annotations

import math

import pytest

from config.ransomware.rw1003_canonical_inference import (
    HIGH_RISK_THRESHOLD,
    INVESTIGATE_THRESHOLD,
    _calibrate_probability,
    _decision,
    _stacking_probability,
)


def test_decision_thresholds_are_frozen() -> None:
    assert _decision(HIGH_RISK_THRESHOLD) == "high_risk"
    assert _decision(INVESTIGATE_THRESHOLD) == "investigate"
    assert _decision(INVESTIGATE_THRESHOLD - 1e-9) == "normal"


def test_energy_uses_sector_specific_calibrator() -> None:
    payload = {
        "method": "sigmoid_probability_calibration",
        "global_calibrator": {
            "coefficient": 0.014902812639115562,
            "intercept": -1.1515236981970445,
        },
        "sector_calibrators": {
            "energy": {
                "coefficient": 0.0316337124133443,
                "intercept": -0.8874865192230148,
                "status": "sector_specific",
            },
            "petrochemical": {
                "fallback": "global_sigmoid",
                "status": "insufficient_class_diversity",
            },
        },
    }

    probability, source = _calibrate_probability(payload, "energy", 0.5)

    assert source == "sector_specific"
    assert 0.0 < probability < 1.0


def test_petrochemical_uses_global_fallback() -> None:
    payload = {
        "method": "sigmoid_probability_calibration",
        "global_calibrator": {
            "coefficient": 0.014902812639115562,
            "intercept": -1.1515236981970445,
        },
        "sector_calibrators": {
            "energy": {
                "coefficient": 0.0316337124133443,
                "intercept": -0.8874865192230148,
                "status": "sector_specific",
            },
            "petrochemical": {
                "fallback": "global_sigmoid",
                "status": "insufficient_class_diversity",
            },
        },
    }

    probability, source = _calibrate_probability(
        payload,
        "petrochemical",
        0.5,
    )

    assert source == "global_fallback"
    assert 0.0 < probability < 1.0


def test_stacking_preserves_temporal_missing_contract() -> None:
    payload = {
        "intercept": -0.5495017677923458,
        "coefficients": {
            "rule_score": 0.5428174934046955,
            "anomaly_score": -0.6298863433001316,
            "catboost_score": 0.8105926128325462,
            "temporal_score": 0.0,
            "graph_score": -0.005783713723105326,
            "rules_missing": 0.0,
            "anomaly_missing": 0.0,
            "catboost_missing": 0.0,
            "temporal_missing": -0.5495017677923458,
            "graph_missing": 0.0,
        },
        "score_standardization": {
            "mean": {
                "rule_score": 0.08024707407407407,
                "anomaly_score": 0.7232614537037036,
                "catboost_score": 0.2753657962962963,
                "temporal_score": 0.0,
                "graph_score": 0.12000000000000002,
            },
            "scale": {
                "rule_score": 0.08327632435004424,
                "anomaly_score": 0.40862690884702807,
                "catboost_score": 0.3018011836339404,
                "temporal_score": 1.0,
                "graph_score": 0.2683281572999748,
            },
        },
    }

    probability = _stacking_probability(
        payload,
        rule_score=0.1,
        anomaly_score=0.7,
        catboost_score=0.3,
        graph_score=0.1,
    )

    assert math.isfinite(probability)
    assert 0.0 < probability < 1.0


def test_invalid_sector_rejected() -> None:
    payload = {
        "global_calibrator": {
            "coefficient": 1.0,
            "intercept": 0.0,
        },
        "sector_calibrators": {},
    }

    with pytest.raises(ValueError, match="Unsupported sector"):
        _calibrate_probability(payload, "unknown", 0.5)

def test_canonical_inference_executes_real_synthetic_row() -> None:
    from datetime import datetime

    from config.ransomware.baselines import RobustAnomalyBaseline
    from config.ransomware.catboost_trainer import (
        build_rows,
        load_and_verify_scenarios,
    )
    from config.ransomware.features.window_features import (
        extract_window_features,
    )
    from config.ransomware.rw0901_oof_scores import (
        _anomaly_score,
        _graph_score,
        _rule_score,
    )
    from config.ransomware.rw1003_canonical_inference import (
        canonical_inference,
    )
    from config.ransomware.scenarios.scenario_event_assembler import (
        assemble_scenario_events,
    )

    _, frozen = load_and_verify_scenarios()
    rows, feature_names = build_rows(frozen)

    baseline = RobustAnomalyBaseline(feature_names)
    baseline.fit(
        [row.features for row in rows if row.split == "train"]
    )

    row = rows[0]
    scenario = next(
        scenario
        for scenario in frozen
        if scenario.scenario_id == row.scenario_id
    )

    events = assemble_scenario_events(scenario)
    end_time = datetime.fromisoformat(
        events[-1].event_time.replace("Z", "+00:00")
    )

    features = extract_window_features(
        events,
        end_time=end_time,
        duration_minutes=row.window_minutes,
    )

    evidence = baseline.score(features)

    rule_score = _rule_score(features)
    anomaly_score = _anomaly_score(evidence)
    graph_score = _graph_score(
        row.industry,
        events,
        end_time,
        row.window_minutes,
    )[0]

    result = canonical_inference(
        observable_features=features,
        industry=row.industry,
        site_types=row.site_types,
        rule_score=rule_score,
        anomaly_score=anomaly_score,
        graph_score=graph_score,
        sector=row.industry,
    )

    assert result["bundle_version"] == "rw0906_v1"
    assert result["task"] == "RW-100-3"
    assert result["sector"] == row.industry
    assert result["decision"] == "investigate"

    assert math.isclose(
        result["probabilities"]["catboost"],
        0.46896461810331674,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        result["probabilities"]["stacked"],
        0.44491388384206043,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        result["probabilities"]["calibrated"],
        0.2901850989809835,
        rel_tol=0.0,
        abs_tol=1e-12,
    )

    assert result["components"]["temporal_score"] is None
    assert result["components"]["temporal_missing"] == 1

    assert result["runtime_contract"] == {
        "synthetic_only": True,
        "human_approval_required": True,
        "real_action_executed": False,
        "operational_state_claimed": False,
        "physical_safety_determination": "not_determined",
    }
