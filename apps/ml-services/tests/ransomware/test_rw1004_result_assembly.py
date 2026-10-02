import pytest

from config.ransomware.rw1004_result_assembly import (
    INCIDENT_STAGES,
    SEVERITIES,
    assemble_result,
)


def test_assemble_result_matches_canonical_contract():
    result = assemble_result(
        use_case="ransomware_resilience",
        industry="energy",
        site_id="synthetic-site-001",
        site_type="control_centre",
        decision="investigate",
        confidence=0.2901850989809835,
        incident_stage="precursor",
        severity="medium",
        data_provenance="LIVE_MODEL",
        warnings=["Temporal challenger unavailable."],
    )

    assert result["use_case"] == "ransomware_resilience"
    assert result["industry"] == "energy"
    assert result["decision"] == "investigate"
    assert result["incident_stage"] == "precursor"
    assert result["confidence"] == 0.2901850989809835
    assert result["severity"] == "medium"
    assert result["affected_assets"] == []
    assert result["suspected_assets"] == []
    assert result["warnings"] == ["Temporal challenger unavailable."]
    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False


def test_affected_and_suspected_assets_remain_separate():
    result = assemble_result(
        use_case="ransomware_resilience",
        industry="energy",
        site_id="synthetic-site-001",
        site_type="substation",
        decision="high_risk",
        confidence=0.8,
        incident_stage="lateral_movement",
        severity="high",
        affected_assets=["asset-a"],
        suspected_assets=["asset-b"],
    )

    assert result["affected_assets"] == ["asset-a"]
    assert result["suspected_assets"] == ["asset-b"]


def test_overlapping_asset_categories_are_rejected():
    with pytest.raises(ValueError, match="both affected and suspected"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="substation",
            decision="investigate",
            confidence=0.5,
            incident_stage="precursor",
            severity="medium",
            affected_assets=["asset-a"],
            suspected_assets=["asset-a"],
        )


def test_safety_invariants_cannot_be_disabled():
    with pytest.raises(ValueError, match="human_approval_required"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="control_centre",
            decision="normal",
            confidence=0.1,
            incident_stage="none",
            severity="low",
            human_approval_required=False,
        )

    with pytest.raises(ValueError, match="real_action_executed"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="control_centre",
            decision="normal",
            confidence=0.1,
            incident_stage="none",
            severity="low",
            real_action_executed=True,
        )


def test_invalid_stage_and_severity_are_rejected():
    with pytest.raises(ValueError, match="incident_stage"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="control_centre",
            decision="normal",
            confidence=0.1,
            incident_stage="unsafe_stage",
            severity="low",
        )

    with pytest.raises(ValueError, match="severity"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="control_centre",
            decision="normal",
            confidence=0.1,
            incident_stage="none",
            severity="unsafe_severity",
        )


def test_confidence_is_bounded():
    with pytest.raises(ValueError, match="between 0 and 1"):
        assemble_result(
            use_case="ransomware_resilience",
            industry="energy",
            site_id="synthetic-site-001",
            site_type="control_centre",
            decision="normal",
            confidence=1.1,
            incident_stage="none",
            severity="low",
        )


def test_real_canonical_inference_assembles_full_result():
    from config.ransomware.rw1003_canonical_inference import canonical_inference
    from config.ransomware.rw1004_result_assembly import assemble_canonical_result

    inference = canonical_inference(
        observable_features={
            "alarm_support_health_ratio": 1.0,
            "asset_evidence_count": 1.0,
            "auth_failure_count": 0.0,
            "backup_age_minutes": 10.0,
            "backup_evidence_count": 1.0,
            "backup_failure_streak": 0.0,
            "batch_quality_dependency_exposure_count": 0.0,
            "communications_health_ratio": 1.0,
            "context_evidence_count": 0.0,
            "critical_service_exposure_count": 0.0,
            "criticality_score": 0.0,
            "dcs_support_exposure_count": 0.0,
            "distinct_source_host_count": 0.0,
            "endpoint_evidence_count": 0.0,
            "entropy_proxy": 0.0,
            "event_count": 1.0,
            "extension_change_ratio": 0.0,
            "file_evidence_count": 0.0,
            "graph_evidence_count": 0.0,
            "identity_evidence_count": 0.0,
            "immutable_copy_present_count": 1.0,
            "ingestion_lag_seconds": 0.0,
            "late_event_ratio": 0.0,
            "maintenance_approval_ratio": 1.0,
            "missing_source_mask": 0.0,
            "network_evidence_count": 0.0,
            "new_peer_ratio": 0.0,
            "new_source_relationship_count": 0.0,
            "observable_value_max": 1.0,
            "observable_value_mean": 1.0,
            "outbound_bytes": 0.0,
            "privilege_change_count": 0.0,
            "protected_boundary_hops": 0.0,
            "quality_evidence_count": 0.0,
            "rare_process_chain_score": 0.0,
            "recovery_tier": 1.0,
            "relay_management_adjacency_count": 0.0,
            "remote_admin_peer_count": 0.0,
            "rename_rate": 0.0,
            "restore_test_age_days": 1.0,
            "scada_visibility_ratio": 1.0,
            "service_availability_ratio": 1.0,
            "service_evidence_count": 0.0,
            "sis_esd_adjacency_count": 0.0,
            "stage_transition_score": 0.0,
            "stale_data_ratio": 0.0,
            "substation_support_exposure_count": 0.0,
            "task_service_creation_count": 0.0,
            "unique_asset_count": 1.0,
            "unique_evidence_type_count": 1.0,
            "unsigned_burst_count": 0.0,
            "window_duration_minutes": 1.0,
            "write_rate": 0.0,
            "zone_crossing_count": 0.0,
        },
        industry="energy",
        site_types="control_centre|substation",
        rule_score=0.0,
        anomaly_score=0.143433,
        graph_score=0.72,
        sector="energy",
    )

    result = assemble_canonical_result(
        canonical_inference=inference,
        use_case="ransomware_resilience",
        site_id="synthetic-site-001",
        site_type="control_centre",
        incident_stage="precursor",
        severity="medium",
        suspected_assets=["asset-a"],
        warnings=["Temporal challenger unavailable."],
    )

    assert result["decision"] == inference["decision"]
    assert result["confidence"] == inference["probabilities"]["calibrated"]
    assert result["industry"] == "energy"
    assert result["site_id"] == "synthetic-site-001"
    assert result["suspected_assets"] == ["asset-a"]
    assert result["affected_assets"] == []
    assert result["human_approval_required"] is True
    assert result["real_action_executed"] is False
    assert result["artifact_provenance"][0]["bundle_version"] == "rw0906_v1"
    assert result["data_provenance"] == "LIVE_MODEL"
