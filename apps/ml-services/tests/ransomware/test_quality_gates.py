from config.ransomware.shared.validation.quality_gates import (
    calculate_quality_gates,
)


def valid_event(event_id="evt-001"):
    return {
        "event_id": event_id,
        "event_time": "2026-01-01T06:30:00Z",
        "ingest_time": "2026-01-01T06:30:05Z",
        "industry": "energy",
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-identity-001",
        "zone": "enterprise_it",
        "metrics": {"risk_score": 0.5},
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