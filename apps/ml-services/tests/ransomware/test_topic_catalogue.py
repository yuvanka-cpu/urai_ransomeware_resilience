from pathlib import Path


CATALOGUE = Path("config/ransomware/shared/topics/topic_catalogue.md")


def test_topic_catalogue_exists():
    assert CATALOGUE.exists()


def test_required_topics_are_registered():
    text = CATALOGUE.read_text(encoding="utf-8")

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


def test_required_topic_keys_are_documented():
    text = CATALOGUE.read_text(encoding="utf-8")

    assert "source_system + event_id" in text
    assert "site_id + asset_id" in text
    assert "asset_id" in text
    assert "incident_id + event_id" in text


def test_normalized_partition_contract_is_documented():
    text = CATALOGUE.read_text(encoding="utf-8")

    assert "site_id + asset_id" in text
    assert "Global ordering is not guaranteed." in text
    assert "event_time" in text
    assert "watermarks" in text
    assert "correlation identifiers" in text


def test_topic_safety_boundary_is_documented():
    text = CATALOGUE.read_text(encoding="utf-8")

    assert "protected" in text
    assert "OT or safety systems" in text
    assert "autonomous isolation" in text
    assert "account disabling" in text
    assert "recovery execution" in text
