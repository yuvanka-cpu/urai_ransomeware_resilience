from app.policies.ransomware_safety import enforce_safety_invariants


def test_rw1105_forces_human_approval():
    result = {
        "human_approval_required": False,
        "real_action_executed": True,
        "warnings": [],
    }

    enforce_safety_invariants(result)

    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False


def test_rw1105_forces_physical_safety_not_determined():
    result = {
        "human_approval_required": True,
        "real_action_executed": False,
        "operational_dependency_impact": [
            {
                "physical_safety_determination": "safe",
                "operational_state_claimed": True,
            }
        ],
        "warnings": [],
    }

    enforce_safety_invariants(result)

    impact = result["operational_dependency_impact"][0]
    assert impact["physical_safety_determination"] == "not_determined"
    assert impact["operational_state_claimed"] is False


def test_rw1105_adds_mandatory_synthetic_warning():
    result = {
        "human_approval_required": True,
        "real_action_executed": False,
        "warnings": [],
    }

    enforce_safety_invariants(result)

    assert any(
        "physical safety is not determined" in warning
        for warning in result["warnings"]
    )


def test_rw1105_preserves_existing_warnings():
    result = {
        "human_approval_required": True,
        "real_action_executed": False,
        "warnings": ["Existing dependency warning"],
    }

    enforce_safety_invariants(result)

    assert "Existing dependency warning" in result["warnings"]
    assert len(result["warnings"]) == 2
