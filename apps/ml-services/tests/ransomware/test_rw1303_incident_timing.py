"""Tests for RW-130-3 offline incident timing metrics."""

from copy import deepcopy

from config.ransomware.rw1303_incident_timing import calculate_incident_timing


def incident(incident_id="INC-001"):
    return {
        "incident_id": incident_id,
        "incident_onset_at": "2026-10-01T10:00:00Z",
        "detected_at": "2026-10-01T10:05:00Z",
        "response_started_at": "2026-10-01T10:08:00Z",
        "recovery_completed_at": "2026-10-01T10:30:00Z",
    }


def test_complete_incident():
    result = calculate_incident_timing([incident()])
    assert result["status"] == "available"
    assert result["metrics"]["mttd"]["mean_minutes"] == 5
    assert result["metrics"]["mean_response_time"]["mean_minutes"] == 3
    assert result["metrics"]["mean_recovery_time"]["mean_minutes"] == 30


def test_multiple_incidents_average():
    second = incident("INC-002")
    second["detected_at"] = "2026-10-01T10:15:00Z"
    second["response_started_at"] = "2026-10-01T10:20:00Z"
    result = calculate_incident_timing([incident(), second])
    assert result["metrics"]["mttd"]["mean_minutes"] == 10
    assert result["metrics"]["mean_response_time"]["mean_minutes"] == 4


def test_missing_detection_partial():
    record = incident()
    record["detected_at"] = None
    record["response_started_at"] = None
    result = calculate_incident_timing([record])
    assert result["status"] == "partial"
    assert result["metrics"]["mttd"]["status"] == "unavailable"
    assert result["metrics"]["mean_recovery_time"]["mean_minutes"] == 30


def test_no_timestamps_unavailable():
    record = {"incident_id": "INC-001"}
    result = calculate_incident_timing([record])
    assert result["status"] == "unavailable"
    assert result["metrics"]["mttd"]["mean_minutes"] is None


def test_empty_list_unavailable():
    assert calculate_incident_timing([])["status"] == "unavailable"


def test_invalid_input_unavailable():
    assert calculate_incident_timing("invalid")["status"] == "unavailable"


def test_duplicate_id_unavailable():
    assert calculate_incident_timing(
        [incident(), incident()]
    )["status"] == "unavailable"


def test_missing_id_unavailable():
    record = incident()
    del record["incident_id"]
    assert calculate_incident_timing([record])["status"] == "unavailable"


def test_invalid_timestamp_unavailable():
    record = incident()
    record["detected_at"] = "not-a-date"
    assert calculate_incident_timing([record])["status"] == "unavailable"


def test_naive_timestamp_unavailable():
    record = incident()
    record["detected_at"] = "2026-10-01T10:05:00"
    assert calculate_incident_timing([record])["status"] == "unavailable"


def test_reversed_chronology_unavailable():
    record = incident()
    record["detected_at"] = "2026-10-01T09:55:00Z"
    assert calculate_incident_timing([record])["status"] == "unavailable"


def test_timezone_offsets():
    record = incident()
    record["detected_at"] = "2026-10-01T15:35:00+05:30"
    result = calculate_incident_timing([record])
    assert result["status"] == "available"
    assert result["metrics"]["mttd"]["mean_minutes"] == 5


def test_excluded_count():
    incomplete = {"incident_id": "INC-002"}
    result = calculate_incident_timing([incident(), incomplete])
    assert result["metrics"]["mttd"]["sample_count"] == 1
    assert result["metrics"]["mttd"]["excluded_count"] == 1


def test_zero_duration_allowed():
    record = incident()
    record["detected_at"] = record["incident_onset_at"]
    record["response_started_at"] = record["incident_onset_at"]
    result = calculate_incident_timing([record])
    assert result["metrics"]["mttd"]["mean_minutes"] == 0
    assert result["metrics"]["mean_response_time"]["mean_minutes"] == 0
