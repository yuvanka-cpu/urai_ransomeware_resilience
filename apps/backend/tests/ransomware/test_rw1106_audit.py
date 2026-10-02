from app.audit.ransomware_audit import build_audit_event


def test_rw1106_audit_event_contains_required_trace_context():
    event = build_audit_event(
        request_id="rw-request-001",
        trace_id="trace-001",
        scenario_id="rw-stage11-route-contract",
        artifact_versions=["rw0906_v1"],
        data_provenance="LIVE_MODEL",
        warnings=["Synthetic defensive analysis only."],
        latency_ms=42.5,
        recommendation_review_state="pending_human_review",
    )

    assert event["event_type"] == "ransomware_orchestration"
    assert event["request_id"] == "rw-request-001"
    assert event["trace_id"] == "trace-001"
    assert event["scenario_id"] == "rw-stage11-route-contract"
    assert event["artifact_versions"] == ["rw0906_v1"]
    assert event["data_provenance"] == "LIVE_MODEL"
    assert event["warnings"] == ["Synthetic defensive analysis only."]
    assert event["latency_ms"] == 42.5
    assert event["recommendation_review_state"] == "pending_human_review"


def test_rw1106_audit_event_preserves_multiple_artifacts_and_warnings():
    event = build_audit_event(
        request_id="rw-request-002",
        trace_id="trace-002",
        scenario_id="rw-stage11-route-contract",
        artifact_versions=["rw0906_v1", "rw1007_latency"],
        data_provenance="DERIVED_BY_BACKEND",
        warnings=["warning-a", "warning-b"],
        latency_ms=None,
        recommendation_review_state="not_applicable",
    )

    assert len(event["artifact_versions"]) == 2
    assert event["warnings"] == ["warning-a", "warning-b"]
    assert event["latency_ms"] is None
