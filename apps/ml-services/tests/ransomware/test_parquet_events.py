from pathlib import Path

from config.ransomware.shared.validation.canonical_event_validator import (
    validate_event,
)
from config.ransomware.shared.validation.parquet_events import (
    read_canonical_events,
)


ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = (
    ROOT / "artifacts/ransomware/offline/canonical_event_snapshot.parquet"
)


def test_read_canonical_events_decodes_structured_fields():
    events = read_canonical_events(PARQUET_PATH)

    assert len(events) == 1

    event = events[0]

    assert isinstance(event["attributes"], dict)
    assert isinstance(event["metrics"], dict)
    assert isinstance(event["quality_flags"], list)

    assert event["attributes"] == {"test": "offline"}
    assert event["metrics"] == {"risk_score": 0.5}
    assert event["quality_flags"] == []


def test_read_canonical_events_preserves_canonical_fields():
    event = read_canonical_events(PARQUET_PATH)[0]

    assert event["event_id"] == "evt-offline-001"
    assert event["schema_version"] == "1.0"
    assert event["industry"] == "energy"
    assert event["data_provenance"] == "SYNTHETIC_GROUND_TRUTH"

def test_offline_canonical_event_passes_validator():
    event = read_canonical_events(PARQUET_PATH)[0]

    assert validate_event(event) == []
