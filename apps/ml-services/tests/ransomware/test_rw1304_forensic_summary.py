"""Tests for RW-130-4 offline synthetic forensic evidence summary."""

from dataclasses import replace

from config.ransomware.rw1304_forensic_summary import summarize_forensic_events
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
    sequence_fingerprint,
)


def event(index=0, **changes):
    values = {
        "scenario_id": "synthetic-001",
        "scenario_seed": 42,
        "split": "train",
        "sequence_index": index,
        "event_time": f"2026-01-01T06:{index:02d}:00Z",
        "event_family": "authentication",
        "event_type": "login_observation",
        "asset_id": "asset-01",
        "attributes": {"observable_value": 0.4},
    }
    values.update(changes)
    return ObservableScenarioEvent(**values)


def test_single_event_summary():
    result = summarize_forensic_events([event()])
    assert result["status"] == "available"
    assert result["event_count"] == 1
    assert result["observed_asset_ids"] == ["asset-01"]


def test_event_family_counts():
    result = summarize_forensic_events([
        event(0),
        event(1),
        event(2, event_family="network"),
    ])
    assert result["event_family_counts"] == {
        "authentication": 2,
        "network": 1,
    }


def test_observed_assets_are_unique_and_sorted():
    result = summarize_forensic_events([
        event(0, asset_id="asset-b"),
        event(1, asset_id="asset-a"),
        event(2, asset_id="asset-b"),
    ])
    assert result["observed_asset_ids"] == ["asset-a", "asset-b"]


def test_unsorted_input_is_ordered():
    result = summarize_forensic_events([event(2), event(0), event(1)])
    assert [item["sequence_index"] for item in result["timeline"]] == [
        0, 1, 2,
    ]


def test_fingerprint_matches_existing_function():
    records = [event(0), event(1)]
    result = summarize_forensic_events(records)
    assert result["sequence_fingerprint_sha256"] == sequence_fingerprint(
        records
    )


def test_empty_events_unavailable():
    assert summarize_forensic_events([])["status"] == "unavailable"


def test_invalid_record_unavailable():
    assert summarize_forensic_events([{"event_type": "test"}])[
        "status"
    ] == "unavailable"


def test_duplicate_index_unavailable():
    assert summarize_forensic_events([
        event(0),
        event(0),
    ])["status"] == "unavailable"


def test_multiple_scenarios_unavailable():
    assert summarize_forensic_events([
        event(0),
        event(1, scenario_id="synthetic-002"),
    ])["status"] == "unavailable"


def test_invalid_timestamp_unavailable():
    assert summarize_forensic_events([
        event(0, event_time="not-a-timestamp"),
    ])["status"] == "unavailable"


def test_reversed_chronology_unavailable():
    assert summarize_forensic_events([
        event(0, event_time="2026-01-01T06:10:00Z"),
        event(1, event_time="2026-01-01T06:00:00Z"),
    ])["status"] == "unavailable"


def test_truth_field_rejected():
    assert summarize_forensic_events([
        event(0, attributes={"ground_truth": "attack"}),
    ])["status"] == "unavailable"


def test_nested_truth_field_rejected():
    assert summarize_forensic_events([
        event(0, attributes={
            "nested": [{"incident_stage_truth": "encryption"}],
        }),
    ])["status"] == "unavailable"


def test_nonfinite_attribute_rejected():
    assert summarize_forensic_events([
        event(0, attributes={"value": float("nan")}),
    ])["status"] == "unavailable"


def test_missing_asset_rejected():
    assert summarize_forensic_events([
        event(0, asset_id=""),
    ])["status"] == "unavailable"


def test_timezone_aware_timestamp_accepted():
    result = summarize_forensic_events([
        event(0, event_time="2026-01-01T11:30:00+05:30"),
    ])
    assert result["status"] == "available"


def test_fingerprint_does_not_cover_timestamps():
    first = [event(0)]
    second = [
        replace(first[0], event_time="2026-01-02T06:00:00Z")
    ]
    first_result = summarize_forensic_events(first)
    second_result = summarize_forensic_events(second)

    assert (
        first_result["sequence_fingerprint_sha256"]
        == second_result["sequence_fingerprint_sha256"]
    )
    assert first_result["first_event_at"] != second_result["first_event_at"]
