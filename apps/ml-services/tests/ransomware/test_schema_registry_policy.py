from pathlib import Path


POLICY = Path(
    "config/ransomware/shared/schemas/schema_registry_policy.md"
)


def test_registry_policy_exists():
    assert POLICY.exists()


def test_key_and_value_schemas_are_separate():
    text = POLICY.read_text()
    assert "Key schema defines" in text
    assert "Value schema defines" in text


def test_backward_is_default():
    text = POLICY.read_text()
    assert "Default compatibility mode: `BACKWARD`." in text


def test_full_requires_justification_and_tests():
    text = POLICY.read_text()
    assert "`FULL` compatibility requires explicit justification and automated tests." in text


def test_breaking_changes_require_versioning():
    text = POLICY.read_text()
    assert "Breaking changes require a new schema version or a new major topic version." in text
