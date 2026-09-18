from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config/ransomware/shared/schemas/canonical_event.avsc"
PARQUET_PATH = (
    ROOT / "artifacts/ransomware/offline/canonical_event_snapshot.parquet"
)


def test_parquet_snapshot_exists():
    assert PARQUET_PATH.exists()


def test_parquet_columns_match_canonical_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    expected = [field["name"] for field in schema["fields"]]

    frame = pd.read_parquet(PARQUET_PATH)

    assert list(frame.columns) == expected


def test_parquet_contains_one_canonical_event():
    frame = pd.read_parquet(PARQUET_PATH)

    assert len(frame) == 1
    assert frame.iloc[0]["schema_version"] == "1.0"
    assert frame.iloc[0]["industry"] == "energy"
