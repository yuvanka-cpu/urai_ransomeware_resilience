import json
from pathlib import Path

from config.ransomware.shared.zone_contract import is_valid_zone


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
)


def load_assets(sector: str):
    asset_file = CONFIG_ROOT / sector / "assets.json"
    return json.loads(
        asset_file.read_text(encoding="utf-8")
    )["assets"]

def test_all_energy_assets_have_valid_zones():
    assets = load_assets("energy")

    assert assets
    assert all(
        is_valid_zone(asset["zone"])
        for asset in assets
    )


def test_all_petrochemical_assets_have_valid_zones():
    assets = load_assets("petrochemical")

    assert assets
    assert all(
        is_valid_zone(asset["zone"])
        for asset in assets
    )


def test_all_canonical_assets_have_exactly_one_zone():
    for sector in ("energy", "petrochemical"):
        assets = load_assets(sector)

        for asset in assets:
            assert isinstance(asset["zone"], str)
            assert asset["zone"]
