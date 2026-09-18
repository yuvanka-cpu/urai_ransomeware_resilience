from pathlib import Path


CATALOGUE = Path("config/ransomware/shared/topics/topic_catalogue.md")


def test_topic_catalogue_exists():
    assert CATALOGUE.exists()


def test_required_topics_are_defined():
    text = CATALOGUE.read_text()

    required_topics = [
        "ransomware.raw.v1",
        "ransomware.normalized.v1",
        "ransomware.reference.v1",
        "ransomware.feature-window.v1",
        "ransomware.incident-evidence.v1",
        "ransomware.dlq.v1",
    ]

    for topic in required_topics:
        assert topic in text


def test_normalized_topic_uses_required_key():
    text = CATALOGUE.read_text()
    assert "`site_id + asset_id`" in text


def test_partition_and_order_contract_is_documented():
    text = CATALOGUE.read_text()
    assert "Global event ordering is not guaranteed." in text
    assert "event_time" in text
    assert "watermarks" in text
    assert "correlation identifiers" in text


def test_raw_events_are_not_used_directly_for_features():
    text = CATALOGUE.read_text()
    assert "Raw events are never used directly for feature engineering." in text
