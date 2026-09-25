from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from config.ransomware.shared.validation.canonical_event_validator import (
    validate_event,
)
from config.ransomware.shared.validation.parquet_events import (
    read_canonical_events,
)
from config.ransomware.shared.validation.quality_gates import (
    calculate_quality_gates,
    load_known_assets,
)


def validate_parquet(
    path: Path,
    config_root: Path,
) -> dict[str, Any]:
    events = read_canonical_events(path)

    event_results = []
    validated_events = []

    for event in events:
        errors = validate_event(event)

        validated_event = dict(event)
        validated_event["_validation_errors"] = errors
        validated_events.append(validated_event)

        event_results.append(
            {
                "event_id": event.get("event_id"),
                "valid": not errors,
                "errors": errors,
            }
        )

    invalid_count = sum(
        1 for result in event_results if not result["valid"]
    )

    known_assets = load_known_assets(config_root)
    quality_gates = calculate_quality_gates(
        validated_events,
        known_assets,
    )

    return {
        "source": str(path),
        "total_events": len(events),
        "valid_events": len(events) - invalid_count,
        "invalid_events": invalid_count,
        "passed": (
            invalid_count == 0
            and quality_gates["passed"]
        ),
        "quality_gates": quality_gates,
        "events": event_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate canonical ransomware events."
    )
    parser.add_argument("parquet_path", type=Path)
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path(
            "apps/ml-services/config/ransomware"
        ),
        help="Root directory containing ransomware asset catalogues.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path for the JSON validation report.",
    )
    args = parser.parse_args()

    report = validate_parquet(
        args.parquet_path,
        args.config_root,
    )

    print(json.dumps(report, indent=2))

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
