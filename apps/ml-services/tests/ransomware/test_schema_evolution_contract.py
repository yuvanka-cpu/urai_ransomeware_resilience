from pathlib import Path


CONTRACT = Path(
    "config/ransomware/shared/schemas/schema_evolution_contract.md"
)


def test_schema_evolution_contract_exists():
    assert CONTRACT.exists()


def test_optional_fields_require_defaults():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "New optional fields MUST have explicit defaults." in text


def test_field_meaning_and_units_cannot_change():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "The meaning of an existing field MUST NOT change." in text
    assert "The unit of an existing field MUST NOT change." in text


def test_breaking_changes_require_new_version():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Breaking changes MUST NOT be introduced silently." in text
    assert "a new schema version" in text
    assert "breaking schema" in text


def test_backward_compatibility_is_preserved():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Non-breaking additions must preserve the configured BACKWARD compatibility" in text


def test_required_evolution_checks_are_documented():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "non-breaking additions preserve compatibility" in text
    assert "breaking changes are detected and require a new version" in text


def test_safety_boundary_is_documented():
    text = CONTRACT.read_text(encoding="utf-8")

    assert "OT writes" in text
    assert "account disabling" in text
    assert "recovery execution" in text
