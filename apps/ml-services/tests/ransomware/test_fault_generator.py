from config.ransomware.scenarios.fault_generator import (
    FAULT_SCENARIO_FAMILIES,
    generate_fault_events,
)


def test_contains_all_required_fault_families():
    events = generate_fault_events(
        "energy-blr01-asset-engineering-001"
    )

    assert {event.scenario_family for event in events} == set(
        FAULT_SCENARIO_FAMILIES
    )


def test_identifies_telemetry_quality_scenarios():
    events = generate_fault_events(
        "energy-blr01-asset-engineering-001"
    )

    quality_families = {
        event.scenario_family
        for event in events
        if event.telemetry_quality_issue
    }

    assert quality_families == {
        "source_loss",
        "reordered_late_events",
        "partial_evidence",
    }


def test_fault_events_preserve_asset_identity():
    asset_id = "petrochemical-mng01-asset-engineering-001"

    events = generate_fault_events(asset_id)

    assert all(event.asset_id == asset_id for event in events)


def test_fault_generator_executes_no_operations():
    events = generate_fault_events(
        "energy-blr01-asset-engineering-001"
    )

    assert all(
        event.operational_action_executed is False
        for event in events
    )
