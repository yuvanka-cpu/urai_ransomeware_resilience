from config.ransomware.scenarios.scenario_contract import ScenarioConfig


def test_scenario_config_contains_required_fields():
    scenario = ScenarioConfig(
        scenario_id="rw-test-001",
        seed=42,
        industry="energy",
        site="energy-blr01",
        asset_set=["energy-blr01-asset-identity-001"],
        lifecycle_timing={"initial_access": 10},
        event_family_parameters={"identity": {"count": 2}},
        intended_labels={"scenario_type": "normal"},
    )

    assert scenario.scenario_id == "rw-test-001"
    assert scenario.seed == 42
    assert scenario.industry == "energy"
    assert scenario.site == "energy-blr01"
    assert scenario.asset_set
    assert scenario.lifecycle_timing
    assert scenario.event_family_parameters
    assert scenario.intended_labels


def test_scenario_config_is_immutable():
    scenario = ScenarioConfig(
        scenario_id="rw-test-002",
        seed=7,
        industry="petrochemical",
        site="petrochemical-mng01",
        asset_set=[],
        lifecycle_timing={},
        event_family_parameters={},
    )

    try:
        scenario.seed = 8
        assert False
    except AttributeError:
        pass


def test_versioned_scenario_schema_exists():
    from pathlib import Path

    schema = Path(
        "config/ransomware/scenarios/scenario_config.schema.json"
    )

    assert schema.exists()
