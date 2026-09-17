from config.ransomware.shared.zone_contract import (
    ALLOWED_ZONES,
    Zone,
    is_valid_zone,
)


def test_six_canonical_zones_exist():
    assert ALLOWED_ZONES == {
        "enterprise_it",
        "industrial_dmz",
        "operations_support",
        "supervisory_control",
        "field_control",
        "protection_safety",
    }


def test_all_zone_enum_values_are_valid():
    for zone in Zone:
        assert is_valid_zone(zone.value)


def test_invalid_zones_are_rejected():
    assert not is_valid_zone("unknown")
    assert not is_valid_zone("enterprise")
    assert not is_valid_zone("")
