from pathlib import Path


POLICY = Path(
    "config/ransomware/shared/schemas/schema_evolution_policy.md"
)


def test_schema_evolution_policy_exists():
    assert POLICY.exists()


def test_optional_fields_require_defaults():
    text = POLICY.read_text()
    assert "Optional fields must have explicit defaults." in text


def test_field_meaning_and_units_cannot_change():
    text = POLICY.read_text()
    assert "Existing field meaning must never be changed." in text
    assert "Existing field units must never be changed." in text


def test_breaking_changes_require_new_version():
    text = POLICY.read_text()
    assert "Breaking changes require a new schema version." in text
    assert "Breaking topic-level changes require a new major topic version." in text


def test_online_offline_semantics_are_preserved():
    text = POLICY.read_text()
    assert "online and offline processing" in text


def test_automated_evolution_tests_are_required():
    text = POLICY.read_text()
    assert "automated compatibility and evolution tests" in text
