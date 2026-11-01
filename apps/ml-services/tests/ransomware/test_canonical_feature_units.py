from config.ransomware.shared.validation import canonical_feature_units


EXPECTED_UNITS = {
    "backup_age_minutes": "minutes",
    "backup_failure_streak": "count",
    "immutable_copy_present_count": "count",
    "restore_test_age_days": "days",
    "service_availability_ratio": "ratio",
    "ingestion_lag_seconds": "seconds",
    "stale_data_ratio": "ratio",
}


def test_canonical_feature_units_match_contract():
    assert canonical_feature_units.CANONICAL_FEATURE_UNITS == EXPECTED_UNITS


def test_canonical_feature_unit_registry_passes_validation():
    passed, errors = canonical_feature_units.validate_canonical_feature_units()

    assert passed is True
    assert errors == []


def test_missing_canonical_feature_is_rejected(monkeypatch):
    incomplete = dict(EXPECTED_UNITS)
    del incomplete["backup_age_minutes"]

    monkeypatch.setattr(
        canonical_feature_units,
        "CANONICAL_FEATURE_UNITS",
        incomplete,
    )

    passed, errors = canonical_feature_units.validate_canonical_feature_units()

    assert passed is False
    assert any("backup_age_minutes" in error for error in errors)


def test_empty_canonical_unit_is_rejected(monkeypatch):
    invalid = dict(EXPECTED_UNITS)
    invalid["backup_age_minutes"] = ""

    monkeypatch.setattr(
        canonical_feature_units,
        "CANONICAL_FEATURE_UNITS",
        invalid,
    )

    passed, errors = canonical_feature_units.validate_canonical_feature_units()

    assert passed is False
    assert any("backup_age_minutes" in error for error in errors)


def test_incorrect_canonical_unit_is_rejected(monkeypatch):
    invalid = dict(EXPECTED_UNITS)
    invalid["backup_age_minutes"] = "hours"

    monkeypatch.setattr(
        canonical_feature_units,
        "CANONICAL_FEATURE_UNITS",
        invalid,
    )

    passed, errors = canonical_feature_units.validate_canonical_feature_units()

    assert passed is False
    assert any(
        "backup_age_minutes" in error and "minutes" in error
        for error in errors
    )


def test_registered_features_must_exist_in_extractor_output():
    passed, errors = (
        canonical_feature_units.validate_canonical_feature_coverage(
            ["event_count", "backup_failure_streak"]
        )
    )

    assert passed is False
    assert any(
        "backup_age_minutes" in error for error in errors
    )



def test_extractor_output_covers_all_registered_features():
    passed, errors = (
        canonical_feature_units.validate_canonical_feature_coverage(
            list(EXPECTED_UNITS)
        )
    )

    assert passed is True
    assert errors == []
