import pytest

from config.ransomware.shared.identifier_contract import (
    IdentifierType,
    is_valid_identifier,
)


def test_valid_site_identifier():
    assert is_valid_identifier("energy-blr01", IdentifierType.SITE)
    assert is_valid_identifier("petrochemical-ref01", IdentifierType.SITE)


def test_valid_asset_identifier():
    assert is_valid_identifier(
        "energy-blr01-asset-historian-001",
        IdentifierType.ASSET,
    )
    assert is_valid_identifier(
        "petrochemical-ref01-asset-dcs-001",
        IdentifierType.ASSET,
    )


def test_valid_service_identifier():
    assert is_valid_identifier(
        "energy-blr01-svc-scada-support",
        IdentifierType.SERVICE,
    )
    assert is_valid_identifier(
        "petrochemical-ref01-svc-dcs-support",
        IdentifierType.SERVICE,
    )


def test_valid_account_identifier():
    assert is_valid_identifier(
        "energy-blr01-acct-engineering-001",
        IdentifierType.ACCOUNT,
    )


def test_valid_dependency_identifier():
    assert is_valid_identifier(
        "energy-blr01-dep-001",
        IdentifierType.DEPENDENCY,
    )


def test_invalid_identifier_formats_are_rejected():
    assert not is_valid_identifier("wrong-format", IdentifierType.ASSET)
    assert not is_valid_identifier("energy-blr01", IdentifierType.ASSET)
    assert not is_valid_identifier(
        "energy-blr01-asset-historian",
        IdentifierType.ASSET,
    )


def test_identifier_types_do_not_get_mixed():
    identifier = "energy-blr01-asset-historian-001"

    assert is_valid_identifier(identifier, IdentifierType.ASSET)
    assert not is_valid_identifier(identifier, IdentifierType.SITE)
    assert not is_valid_identifier(identifier, IdentifierType.SERVICE)


def test_identifier_values_are_unique():
    asset_ids = [
        "energy-blr01-asset-historian-001",
        "energy-blr01-asset-scada-001",
        "energy-blr01-asset-jumphost-001",
    ]

    assert len(asset_ids) == len(set(asset_ids))