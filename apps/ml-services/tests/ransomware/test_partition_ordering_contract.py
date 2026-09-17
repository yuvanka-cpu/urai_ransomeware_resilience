from pathlib import Path


CONTRACT = Path(
    "config/ransomware/shared/topics/partition_ordering_contract.md"
)


def test_partition_ordering_contract_exists():
    assert CONTRACT.exists()


def test_partition_key_is_site_and_asset():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "site_id + asset_id" in text


def test_global_ordering_is_not_guaranteed():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Global ordering across normalized telemetry is NOT guaranteed." in text


def test_cross_source_timeline_requirements():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "`event_time` for event chronology" in text
    assert "watermarks for event-time progress" in text
    assert "correlation identifiers for cross-source event association" in text


def test_ingest_order_is_not_event_chronology():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Ingest order MUST NOT be treated as event chronology." in text


def test_online_and_offline_semantics_are_aligned():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "both online and offline processing semantics" in text
