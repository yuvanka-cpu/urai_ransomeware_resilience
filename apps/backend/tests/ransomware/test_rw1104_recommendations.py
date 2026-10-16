from app.policies.ransomware_recommendations import assemble_recommendations


def test_rw1104_investigate_recommendation_uses_scored_evidence():
    evidence = ["rule_score=0.42", "anomaly_score=0.31"]

    recommendations = assemble_recommendations(
        decision="investigate",
        evidence=evidence,
    )

    assert recommendations
    assert any("scored evidence" in item for item in recommendations)


def test_rw1104_high_risk_does_not_execute_action():
    recommendations = assemble_recommendations(
        decision="high_risk",
        evidence=["stacked_score=0.81"],
    )

    assert recommendations
    assert not any(
        word in " ".join(recommendations).lower()
        for word in ["execute", "isolate", "disable", "shutdown", "encrypt"]
    )


def test_rw1104_unavailable_does_not_claim_live_inference():
    recommendations = assemble_recommendations(
        decision="unavailable",
        evidence=[],
    )

    assert recommendations
    assert "live-model" in " ".join(recommendations)


def test_rw1104_does_not_create_or_replace_model_decision():
    for decision in ("normal", "investigate", "high_risk", "unavailable"):
        recommendations = assemble_recommendations(
            decision=decision,
            evidence=["synthetic scored evidence"],
        )

        assert not any(
            item.startswith("Decision:")
            for item in recommendations
        )


def test_evidence_aware_guidance():
    recommendations = assemble_recommendations(
        decision="investigate",
        evidence=[
            "rule_score=0.42",
            "anomaly_score=0.31",
            "graph_score=0.72",
            "catboost_score=0.46",
        ],
    )

    text = " ".join(recommendations).lower()

    assert "rule-based detection" in text
    assert "anomaly signal" in text
    assert "relationship and dependency" in text
    assert "catboost classifier" in text


def test_invalid_scores_do_not_generate_signal_guidance():
    recommendations = assemble_recommendations(
        decision="investigate",
        evidence=[
            "rule_score=nan",
            "anomaly_score=2.5",
            "graph_score=invalid",
        ],
    )

    text = " ".join(recommendations).lower()

    assert "supporting model signals are unavailable" in text
    assert "rule-based detection signal" not in text
    assert "relationship and dependency evidence" not in text


def test_unavailable_decision_does_not_generate_playbook_guidance():
    recommendations = assemble_recommendations(
        decision="unavailable",
        evidence=["rule_score=0.8"],
    )

    assert len(recommendations) == 1
    assert "dependency failure" in recommendations[0]


def test_playbook_remains_advisory():
    recommendations = assemble_recommendations(
        decision="high_risk",
        evidence=["rule_score=0.9", "graph_score=0.8"],
    )

    text = " ".join(recommendations).lower()

    assert "human review" in text
    assert not any(
        word in text
        for word in ["execute", "isolate", "disable", "shutdown", "encrypt"]
    )
