from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


JSON_FIELDS = {"attributes", "metrics", "quality_flags"}


def read_canonical_events(path: Path) -> list[dict[str, Any]]:
    """Read canonical events from the project's offline Parquet representation."""
    frame = pd.read_parquet(path)
    events: list[dict[str, Any]] = []

    for row in frame.to_dict(orient="records"):
        event = dict(row)

        for field in JSON_FIELDS:
            if field in event and isinstance(event[field], str):
                event[field] = json.loads(event[field])

            if field == "quality_flags" and hasattr(event[field], "tolist"):
                event[field] = event[field].tolist()

        events.append(event)

    return events
