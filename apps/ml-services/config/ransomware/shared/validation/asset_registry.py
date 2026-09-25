import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]


def load_known_assets() -> set[str]:
    known_assets: set[str] = set()

    for sector in ("energy", "petrochemical"):
        path = BASE_DIR / sector / "assets.json"
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

        for asset in data["assets"]:
            known_assets.add(asset["asset_id"])

    return known_assets


def validate_asset_id(asset_id: str) -> None:
    known_assets = load_known_assets()

    if asset_id not in known_assets:
        raise ValueError(
            f"RW-050-6 orphan asset detected: {asset_id}"
        )
