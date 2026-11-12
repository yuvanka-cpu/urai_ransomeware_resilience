from config.ransomware.shared.validation.quality_gates import (
    calculate_quality_gates,
)


def valid_event(event_id="evt-001"):
    return {
        "event_id": event_id,
        "schema_version": "1.0",
        "event_time": "2026-01-01T06:30:00Z",
        "ingest_time": "2026-01-01T06:30:05Z",
        "industry": "energy",
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-identity-001",
        "zone": "enterprise_it",
        "metrics": {},
        "_validation_errors": [],
    }


KNOWN_ASSETS = {
    "energy": {"energy-blr01-asset-identity-001"},
    "petrochemical": set(),
}


def test_valid_event_passes_quality_gates():
    result = calculate_quality_gates(
        [valid_event()],
        KNOWN_ASSETS,
    )

    assert result["passed"] is True
    assert result["status"] == "PASS"

    units_gate = result["gates"]["canonical_units"]
    assert units_gate["passed"] is True
    assert units_gate["scope"] == (
        "derived_features_and_canonical_event_metrics"
    )
    assert units_gate["metric_units_status"] == (
        "EMPTY_NO_APPROVED_METRICS"
    )
    assert units_gate["metric_registry_valid"] is True
    assert units_gate["registered_event_metrics"] == 0


def test_invalid_schema_fails_schema_gate():
    event = valid_event()
    event["_validation_errors"] = ["invalid event"]

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    assert result["gates"]["schema_validity"]["passed"] is False
    assert result["passed"] is False


def test_missing_required_context_fails_context_gate():
    event = valid_event()
    del event["zone"]

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    assert result["gates"]["required_context"]["passed"] is False
    assert result["passed"] is False


def test_invalid_timestamp_fails_timestamp_gate():
    event = valid_event()
    event["event_time"] = "not-a-timestamp"

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    assert result["gates"]["timestamp_parse_success"]["passed"] is False
    assert result["passed"] is False


def test_unknown_asset_fails_asset_resolution_gate():
    event = valid_event()
    event["asset_id"] = "energy-blr01-asset-unknown-001"

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    assert result["gates"]["known_asset_resolution"]["passed"] is False
    assert result["passed"] is False


def test_duplicate_event_id_fails_duplicate_gate():
    events = [
        valid_event("evt-duplicate"),
        valid_event("evt-duplicate"),
    ]

    result = calculate_quality_gates(
        events,
        KNOWN_ASSETS,
    )

    assert result["gates"]["duplicate_event_id"]["passed"] is False
    assert result["duplicate_event_ids"] == ["evt-duplicate"]
    assert result["passed"] is False


def test_non_numeric_metric_fails_numeric_gate():
    event = valid_event()
    event["metrics"] = {"risk_score": "high"}

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    assert result["gates"]["canonical_numeric_values"]["passed"] is False
    assert result["passed"] is False


def test_unregistered_metric_fails_canonical_units_gate():
    event = valid_event()
    event["metrics"] = {"risk_score": 0.5}

    result = calculate_quality_gates(
        [event],
        KNOWN_ASSETS,
    )

    units_gate = result["gates"]["canonical_units"]
    assert units_gate["passed"] is False
    assert any(
        "unregistered canonical metric 'risk_score'" in error
        for error in units_gate["errors"]
    )
    assert result["passed"] is False
