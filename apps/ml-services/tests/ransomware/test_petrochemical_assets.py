import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ASSET_FILE = (
    REPOSITORY_ROOT
    / "apps"
    / "ml-services"
    / "config"
    / "ransomware"
    / "petrochemical"
    / "assets.json"
)


def load_assets():
    return json.loads(
        ASSET_FILE.read_text(encoding="utf-8")
    )["assets"]


def test_petrochemical_reference_assets_are_unique_and_complete():
    assets = load_assets()

    assert len(assets) == 11

    asset_ids = [asset["asset_id"] for asset in assets]
    assert len(asset_ids) == len(set(asset_ids))

    for asset in assets:
        assert asset["site_id"]
        assert asset["display_name"]
        assert asset["asset_type"]
        assert asset["zone"]
        assert asset["criticality"]
        assert asset["recovery_tier"]


def test_petrochemical_assets_use_petrochemical_site_ids():
    assets = load_assets()

    assert all(
        asset["site_id"].startswith("petrochemical-")
        for asset in assets
    )


def test_petrochemical_assets_have_expected_types():
    assets = load_assets()

    asset_types = {asset["asset_type"] for asset in assets}

    assert asset_types == {
        "identity",
        "vendor_access",
        "industrial_dmz",
        "dcs_hmi_support",
        "engineering_workstation",
        "historian",
        "batch_quality",
        "maintenance",
        "terminal_loading",
        "backup",
        "sis_esd_adjacent",
    }
