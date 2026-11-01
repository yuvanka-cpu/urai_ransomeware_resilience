"""Canonical units for derived ransomware-resilience features."""

from __future__ import annotations


EXPECTED_CANONICAL_FEATURE_UNITS: dict[str, str] = {
    "backup_age_minutes": "minutes",
    "backup_failure_streak": "count",
    "immutable_copy_present_count": "count",
    "restore_test_age_days": "days",
    "service_availability_ratio": "ratio",
    "ingestion_lag_seconds": "seconds",
    "stale_data_ratio": "ratio",
}

CANONICAL_FEATURE_UNITS: dict[str, str] = dict(
    EXPECTED_CANONICAL_FEATURE_UNITS
)


def validate_canonical_feature_units() -> tuple[bool, list[str]]:
    """Validate required feature-unit declarations."""
    errors: list[str] = []

    missing = (
        EXPECTED_CANONICAL_FEATURE_UNITS.keys()
        - CANONICAL_FEATURE_UNITS.keys()
    )
    if missing:
        errors.append(
            f"Missing canonical feature units: {sorted(missing)}"
        )

    for feature, expected_unit in EXPECTED_CANONICAL_FEATURE_UNITS.items():
        actual_unit = CANONICAL_FEATURE_UNITS.get(feature)
        if actual_unit != expected_unit:
            errors.append(
                f"Feature {feature!r} must use unit "
                f"{expected_unit!r}; found {actual_unit!r}."
            )

    for feature, unit in CANONICAL_FEATURE_UNITS.items():
        if not isinstance(feature, str) or not feature.strip():
            errors.append("Feature names must be non-empty strings.")
        if not isinstance(unit, str) or not unit.strip():
            errors.append(
                f"Feature {feature!r} has an invalid canonical unit."
            )

    return not errors, errors


def validate_canonical_feature_coverage(
    feature_names: list[str],
) -> tuple[bool, list[str]]:
    """Ensure every registered unit belongs to an emitted feature."""
    registry_valid, errors = validate_canonical_feature_units()
    available_features = set(feature_names)

    missing = sorted(
        CANONICAL_FEATURE_UNITS.keys() - available_features
    )
    if missing:
        errors.append(
            f"Registered canonical features missing from output: {missing}"
        )

    return registry_valid and not errors, errors
