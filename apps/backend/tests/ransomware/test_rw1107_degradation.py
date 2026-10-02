import pytest

from app.policies.ransomware_degradation import (
    build_degraded_state,
    build_fallback_state,
    build_unavailable_state,
)


@pytest.mark.parametrize(
    "builder,state,provenance",
    [
        (build_degraded_state, "degraded", "UNAVAILABLE"),
        (build_fallback_state, "fallback", "FALLBACK"),
        (build_unavailable_state, "unavailable", "UNAVAILABLE"),
    ],
)
def test_rw1107_safe_degradation_matrix(builder, state, provenance):
    result = builder(
        reason="Synthetic dependency failure",
        request_id="rw-request-001",
        trace_id="trace-001",
    )

    assert result["state"] == state
    assert result["runtime_state"] == state
    assert result["decision"] == "unavailable"
    assert result["data_provenance"] == provenance
    assert result["fallback_is_live_inference"] is False
    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False
    assert result["request_id"] == "rw-request-001"
    assert result["trace_id"] == "trace-001"
    assert result["warnings"]


def test_rw1107_fallback_is_explicitly_marked():
    result = build_fallback_state(
        reason="ML service unavailable",
        request_id="rw-request-002",
        trace_id="trace-002",
    )

    assert any(
        "FALLBACK" in warning
        for warning in result["warnings"]
    )
    assert result["fallback_is_live_inference"] is False
