from config.ransomware.shared.source_event_contract import (
    ALLOWED_EVENT_FAMILIES,
    ALLOWED_SOURCE_SYSTEMS,
    EventFamily,
    SourceSystem,
    is_valid_event_family,
    is_valid_source_system,
)


EXPECTED_CATEGORIES = {
    "endpoint",
    "file",
    "identity",
    "network",
    "backup",
    "service_health",
    "asset",
    "maintenance",
    "synthetic",
}


def test_source_system_enum_contains_registered_categories():
    assert ALLOWED_SOURCE_SYSTEMS == EXPECTED_CATEGORIES


def test_event_family_enum_contains_registered_categories():
    assert ALLOWED_EVENT_FAMILIES == EXPECTED_CATEGORIES


def test_registered_values_are_valid():
    for value in EXPECTED_CATEGORIES:
        assert is_valid_source_system(value)
        assert is_valid_event_family(value)


def test_unregistered_values_are_rejected():
    assert not is_valid_source_system("unknown")
    assert not is_valid_event_family("unknown")
    assert not is_valid_source_system("")
    assert not is_valid_event_family("")


def test_enums_are_string_compatible():
    assert SourceSystem.ENDPOINT.value == "endpoint"
    assert EventFamily.ENDPOINT.value == "endpoint"
