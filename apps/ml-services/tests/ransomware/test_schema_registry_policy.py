from pathlib import Path


POLICY = Path(
    "config/ransomware/shared/schemas/schema_registry_policy.md"
)


def test_schema_registry_policy_exists():
    assert POLICY.exists()


def test_key_and_value_schemas_are_separate():
    text = POLICY.read_text(encoding="utf-8")

    assert "Kafka key schemas and Kafka value schemas MUST be registered separately." in text
    assert "The key schema defines the partition/join identity" in text
    assert "The value schema defines the canonical event" in text


def test_backward_is_default_compatibility():
    text = POLICY.read_text(encoding="utf-8")

    assert "`BACKWARD`" in text
    assert "default compatibility mode" in text


def test_full_requires_justification_and_tests():
    text = POLICY.read_text(encoding="utf-8")

    assert "`FULL`" in text
    assert "documented justification" in text
    assert "explicit compatibility tests" in text


def test_ci_enforces_schema_compatibility():
    text = POLICY.read_text(encoding="utf-8")

    assert "Schema changes MUST be checked in CI before acceptance." in text
    assert "incompatible schema changes fail validation" in text


def test_safety_boundary_is_documented():
    text = POLICY.read_text(encoding="utf-8")

    assert "OT writes" in text
    assert "account disabling" in text
    assert "recovery execution" in text
