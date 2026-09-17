from datetime import datetime

import pytest

from config.ransomware.shared.normalization import (
    normalize_boolean,
    normalize_enum,
    normalize_hash,
    normalize_identifier,
    normalize_ip,
    normalize_list,
    normalize_nested_record,
    normalize_null_or_sentinel,
    normalize_number,
    normalize_timestamp,
    normalize_unit,
)


def test_timestamp_normalizes_to_utc():
    assert (
        normalize_timestamp("2026-01-01T12:00:00+05:30")
        == "2026-01-01T06:30:00Z"
    )


def test_timestamp_rejects_missing_timezone():
    with pytest.raises(ValueError):
        normalize_timestamp("2026-01-01T12:00:00")


def test_number_normalizes_numeric_values():
    assert normalize_number("42.5") == 42.5
    assert normalize_number(10) == 10.0


def test_number_does_not_convert_invalid_values_to_zero():
    with pytest.raises(ValueError):
        normalize_number("not-a-number")


def test_boolean_normalizes_common_values():
    assert normalize_boolean("true") is True
    assert normalize_boolean("FALSE") is False
    assert normalize_boolean(1) is True
    assert normalize_boolean(0) is False


def test_boolean_rejects_invalid_values():
    with pytest.raises(ValueError):
        normalize_boolean("maybe")


def test_enum_accepts_registered_values_only():
    allowed = {"low", "medium", "high"}

    assert normalize_enum("HIGH", allowed) == "high"

    with pytest.raises(ValueError):
        normalize_enum("critical", allowed)


def test_ip_normalizes_valid_address():
    assert normalize_ip(" 192.168.1.10 ") == "192.168.1.10"


def test_ip_rejects_invalid_address():
    with pytest.raises(ValueError):
        normalize_ip("999.999.999.999")


def test_identifier_is_normalized_without_changing_structure():
    assert (
        normalize_identifier(" ENERGY-BLR01-ASSET-IDENTITY-001 ")
        == "energy-blr01-asset-identity-001"
    )


def test_identifier_rejects_invalid_value():
    with pytest.raises(ValueError):
        normalize_identifier("bad identifier!")


def test_hash_is_normalized_to_lowercase():
    assert normalize_hash("ABCDEF1234") == "abcdef1234"


def test_hash_rejects_non_hex_value():
    with pytest.raises(ValueError):
        normalize_hash("not-a-hash")


def test_list_normalizes_supported_inputs():
    assert normalize_list(["a", "b"]) == ["a", "b"]
    assert normalize_list(("a", "b")) == ["a", "b"]
    assert normalize_list("a, b, c") == ["a", "b", "c"]


def test_nested_record_preserves_structure():
    record = {"source": "endpoint", "count": 2}

    assert normalize_nested_record(record) == record


def test_nested_record_rejects_non_object():
    with pytest.raises(ValueError):
        normalize_nested_record(["not", "a", "record"])


def test_null_and_sentinel_values_become_none():
    assert normalize_null_or_sentinel(None) is None
    assert normalize_null_or_sentinel("N/A") is None
    assert normalize_null_or_sentinel("unknown") is None
    assert normalize_null_or_sentinel("actual-value") == "actual-value"


def test_declared_unit_is_retained():
    assert normalize_unit("12.5", "MW") == (12.5, "MW")


def test_declared_unit_is_required():
    with pytest.raises(ValueError):
        normalize_unit("12.5", "")


def test_datetime_input_is_supported():
    value = datetime.fromisoformat("2026-01-01T12:00:00+05:30")

    assert normalize_timestamp(value) == "2026-01-01T06:30:00Z"
