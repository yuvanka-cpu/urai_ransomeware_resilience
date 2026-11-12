import json

import pytest

from config.ransomware.shared.validation import canonical_metric_units as metric_units


def test_empty_registry_is_valid():
    registry = metric_units.load_canonical_metric_unit_registry()

    assert registry["registry_version"] == "1.0"
    assert registry["schema_compatibility"] == ["1.0"]
    assert registry["metrics"] == {}


def test_empty_metrics_pass_for_supported_schema():
    valid, errors = metric_units.validate_canonical_metric_units({}, "1.0")

    assert valid is True
    assert errors == []


def test_unsupported_schema_version_fails():
    valid, errors = metric_units.validate_canonical_metric_units({}, "2.0")

    assert valid is False
    assert any("does not support schema version" in error for error in errors)


def test_unregistered_metric_fails():
    valid, errors = metric_units.validate_canonical_metric_units(
        {"risk_score": 0.5}, "1.0"
    )

    assert valid is False
    assert "metrics: unregistered canonical metric 'risk_score'" in errors


@pytest.mark.parametrize(
    "registry",
    [
        [],
        {"registry_version": "2.0"},
        {
            "registry_version": "1.0",
            "schema_compatibility": [],
            "metrics": {},
        },
        {
            "registry_version": "1.0",
            "schema_compatibility": ["1.0"],
            "metrics": [],
        },
        {
            "registry_version": "1.0",
            "schema_compatibility": ["1.0"],
            "metrics": {"temperature": {}},
        },
        {
            "registry_version": "1.0",
            "schema_compatibility": ["1.0"],
            "metrics": {"temperature": {"unit": ""}},
        },
    ],
)
def test_malformed_registry_is_rejected(tmp_path, monkeypatch, registry):
    registry_path = tmp_path / "canonical_metric_units.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(metric_units, "REGISTRY_PATH", registry_path)

    with pytest.raises(ValueError):
        metric_units.load_canonical_metric_unit_registry()

@pytest.mark.parametrize("content", ["{invalid json", None])
def test_unreadable_or_malformed_registry_is_rejected(
    tmp_path, monkeypatch, content
):
    registry_path = tmp_path / "canonical_metric_units.json"
    if content is not None:
        registry_path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(metric_units, "REGISTRY_PATH", registry_path)

    with pytest.raises(ValueError, match="Cannot load canonical metric-unit registry"):
        metric_units.load_canonical_metric_unit_registry()
