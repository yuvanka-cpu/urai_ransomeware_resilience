"""Machine-readable units for canonical event metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).with_name(
    "canonical_metric_units.json"
)


def load_canonical_metric_unit_registry() -> dict[str, Any]:
    """Load and validate the canonical metric-unit registry."""

    try:
        registry = json.loads(
            REGISTRY_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Cannot load canonical metric-unit registry: {exc}"
        ) from exc

    if not isinstance(registry, dict):
        raise ValueError("Metric-unit registry must be an object")

    if registry.get("registry_version") != "1.0":
        raise ValueError("Unsupported metric-unit registry version")

    compatibility = registry.get("schema_compatibility")
    if (
        not isinstance(compatibility, list)
        or not compatibility
        or not all(
            isinstance(version, str) and version.strip()
            for version in compatibility
        )
    ):
        raise ValueError("Invalid schema compatibility declarations")

    metrics = registry.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Metric registry entries must be an object")

    for name, definition in metrics.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Metric names must be non-empty strings")

        if not isinstance(definition, dict):
            raise ValueError(
                f"Metric {name!r} definition must be an object"
            )

        unit = definition.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError(
                f"Metric {name!r} must declare an explicit unit"
            )

    return registry


def validate_canonical_metric_units(
    metrics: dict[str, Any],
    schema_version: str,
) -> tuple[bool, list[str]]:
    """Reject unregistered metrics and unsupported schema versions."""

    errors: list[str] = []

    try:
        registry = load_canonical_metric_unit_registry()
    except ValueError as exc:
        return False, [str(exc)]

    if schema_version not in registry["schema_compatibility"]:
        errors.append(
            f"Metric registry does not support schema version "
            f"{schema_version!r}"
        )

    registered = registry["metrics"]

    for name in metrics:
        if not isinstance(name, str) or name not in registered:
            errors.append(
                f"metrics: unregistered canonical metric {name!r}"
            )

    return not errors, errors
