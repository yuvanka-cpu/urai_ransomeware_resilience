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
