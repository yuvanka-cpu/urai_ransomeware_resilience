from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "config/ransomware/shared/schemas/canonical_event.avsc"
OUTPUT_PATH = ROOT / "artifacts/ransomware/offline/canonical_event_snapshot.parquet"


def main():
    schema = json.loads(SCHEMA_PATH.read_text())
    field_names = [field["name"] for field in schema["fields"]]

    row = {
        "event_id": "evt-offline-001",
        "event_time": "2026-01-01T06:30:00Z",
        "ingest_time": "2026-01-01T06:30:05Z",
        "schema_version": "1.0",
        "source_system": "synthetic",
        "event_family": "synthetic",
        "event_type": "ransomware_test_event",
        "industry": "energy",
        "site_id": "energy-blr01",
        "asset_id": "energy-blr01-asset-identity-001",
        "zone": "enterprise_it",
        "actor_id": None,
        "severity": "medium",
        "attributes": json.dumps({"test": "offline"}),
        "metrics": json.dumps({"risk_score": 0.5}),
        "quality_flags": json.dumps([]),
        "data_provenance": "SYNTHETIC_GROUND_TRUTH",
        "payload_hash": "a" * 64,
    }

    frame = pd.DataFrame([{name: row[name] for name in field_names}])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT_PATH, index=False)

    print(f"Created: {OUTPUT_PATH}")
    print(f"Columns: {list(frame.columns)}")


if __name__ == "__main__":
    main()
