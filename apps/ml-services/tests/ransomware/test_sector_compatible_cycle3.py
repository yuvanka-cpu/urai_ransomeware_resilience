"""Tests for Cycle 3 sector-compatible synthetic scenario construction."""

import pytest

from config.ransomware.graph_propagation import load_sector_graph
from config.ransomware.scenarios.sector_compatible_cycle3 import (
    Cycle3ScenarioBatch,
    build_sector_compatible_scenarios,
)


@pytest.mark.parametrize("sector", ["energy", "petrochemical"])
def test_default_assets_are_sector_compatible(sector):
    batch = build_sector_compatible_scenarios(sector)
    graph = load_sector_graph(sector)

    assert isinstance(batch, Cycle3ScenarioBatch)
    assert batch.sector == sector
    assert batch.scenarios

    for scenario in batch.scenarios:
        assert scenario.industry == sector
        assert scenario.asset_id in graph.assets


@pytest.mark.parametrize("sector", ["energy", "petrochemical"])
def test_default_batch_contains_all_canonical_assets(sector):
    batch = build_sector_compatible_scenarios(sector)
    graph = load_sector_graph(sector)

    assert set(batch.asset_ids) == set(graph.assets)


def test_energy_asset_identity_preserved():
    asset = "energy-blr01-asset-identity-001"
    batch = build_sector_compatible_scenarios("energy", [asset])

    assert batch.asset_ids == (asset,)
    assert all(scenario.asset_id == asset for scenario in batch.scenarios)


def test_petrochemical_asset_identity_preserved():
    asset = "petrochemical-mng01-asset-identity-001"
    batch = build_sector_compatible_scenarios("petrochemical", [asset])

    assert batch.asset_ids == (asset,)
    assert all(scenario.asset_id == asset for scenario in batch.scenarios)


@pytest.mark.parametrize(
    "sector,asset",
    [
        ("energy", "petrochemical-mng01-asset-identity-001"),
        ("petrochemical", "energy-blr01-asset-identity-001"),
        ("energy", "unknown-asset-999"),
    ],
)
def test_incompatible_assets_rejected(sector, asset):
    with pytest.raises(ValueError):
        build_sector_compatible_scenarios(sector, [asset])


def test_duplicate_assets_rejected():
    asset = "energy-blr01-asset-identity-001"

    with pytest.raises(ValueError):
        build_sector_compatible_scenarios("energy", [asset, asset])


@pytest.mark.parametrize("sector", ["unknown", "", None])
def test_invalid_sector_rejected(sector):
    with pytest.raises(ValueError):
        build_sector_compatible_scenarios(sector)


def test_empty_asset_list_rejected():
    with pytest.raises(ValueError):
        build_sector_compatible_scenarios("energy", [])


def test_deterministic_generation():
    first = build_sector_compatible_scenarios("energy")
    second = build_sector_compatible_scenarios("energy")

    assert first == second


def test_sector_scenarios_are_not_mixed():
    energy = build_sector_compatible_scenarios("energy")
    petrochemical = build_sector_compatible_scenarios("petrochemical")

    assert all(s.industry == "energy" for s in energy.scenarios)
    assert all(s.industry == "petrochemical" for s in petrochemical.scenarios)

    assert set(energy.asset_ids).isdisjoint(petrochemical.asset_ids)


def test_result_is_immutable():
    batch = build_sector_compatible_scenarios(
        "energy",
        ["energy-blr01-asset-identity-001"],
    )

    with pytest.raises(AttributeError):
        batch.sector = "petrochemical"
