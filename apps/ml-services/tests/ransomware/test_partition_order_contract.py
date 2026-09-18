from pathlib import Path


CONTRACT = Path(
    "config/ransomware/shared/topics/partition_order_contract.md"
)


def test_partition_order_contract_exists():
    assert CONTRACT.exists()


def test_normalized_partition_key_is_site_and_asset():
    text = CONTRACT.read_text()
    assert "site_id + asset_id" in text


def test_global_order_is_not_guaranteed():
    text = CONTRACT.read_text()
    assert "Global ordering across all partitions is not guaranteed." in text


def test_cross_source_timeline_requirements_are_defined():
    text = CONTRACT.read_text()
    assert "event_time" in text
    assert "Watermarks" in text
    assert "Correlation identifiers" in text


def test_protected_dependencies_remain_read_only():
    text = CONTRACT.read_text()
    assert "Protected OT dependencies remain read-only." in text
