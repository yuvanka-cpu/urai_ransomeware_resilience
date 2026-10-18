"""Independent tests for Cycle 3 sector-aware asset compatibility."""

import pytest

from config.ransomware.asset_compatibility_cycle3 import (
    AssetCompatibilityResult,
    validate_sector_asset,
)


def test_valid_energy_asset():
    asset_id = "energy-blr01-asset-identity-001"

    result = validate_sector_asset("energy", asset_id)

    assert isinstance(result, AssetCompatibilityResult)
    assert result.sector == "energy"
    assert result.asset_id == asset_id
    assert result.status == "sector_graph_match"
    assert result.compatible is True
    assert result.matched_sector == "energy"


def test_valid_petrochemical_asset():
    asset_id = "petrochemical-mng01-asset-identity-001"

    result = validate_sector_asset("petrochemical", asset_id)

    assert result.status == "sector_graph_match"
    assert result.compatible is True
    assert result.matched_sector == "petrochemical"


def test_cross_sector_asset_is_identified():
    asset_id = "energy-blr01-asset-identity-001"

    result = validate_sector_asset("petrochemical", asset_id)

    assert result.asset_id == asset_id
    assert result.status == "cross_sector_asset"
    assert result.compatible is False
    assert result.matched_sector == "energy"


def test_unknown_asset_is_identified():
    asset_id = "energy-blr01-asset-does-not-exist"

    result = validate_sector_asset("energy", asset_id)

    assert result.asset_id == asset_id
    assert result.status == "absent_from_both_graphs"
    assert result.compatible is False
    assert result.matched_sector is None


@pytest.mark.parametrize(
    "sector",
    ["unknown", "Energy", "", None],
)
def test_invalid_sector_is_rejected(sector):
    with pytest.raises(ValueError):
        validate_sector_asset(
            sector,
            "energy-blr01-asset-identity-001",
        )


@pytest.mark.parametrize(
    "asset_id",
    ["", "   ", None, 123],
)
def test_invalid_asset_id_is_rejected(asset_id):
    with pytest.raises(ValueError):
        validate_sector_asset("energy", asset_id)


def test_result_is_immutable():
    result = validate_sector_asset(
        "energy",
        "energy-blr01-asset-identity-001",
    )

    with pytest.raises(AttributeError):
        result.asset_id = "modified"


def test_asset_identifier_is_never_substituted():
    asset_id = "energy-blr01-asset-engineering-001"

    result = validate_sector_asset("energy", asset_id)

    assert result.asset_id == asset_id
    assert result.status == "absent_from_both_graphs"
    assert result.compatible is False
