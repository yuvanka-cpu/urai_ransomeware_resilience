from config.ransomware.scenarios.lifecycle_generator import (
    LIFECYCLE_STAGES,
    generate_lifecycle,
)


def test_lifecycle_contains_all_required_stages():
    events = generate_lifecycle("energy-blr01-asset-identity-001")

    assert [event.stage for event in events] == list(LIFECYCLE_STAGES)


def test_lifecycle_is_observable_only():
    events = generate_lifecycle("energy-blr01-asset-identity-001")

    assert all(event.observable_only for event in events)


def test_lifecycle_does_not_execute_operations():
    events = generate_lifecycle("energy-blr01-asset-identity-001")

    assert all(event.event_family == "synthetic" for event in events)


def test_lifecycle_preserves_asset_identity():
    asset_id = "petrochemical-mng01-asset-identity-001"

    events = generate_lifecycle(asset_id)

    assert all(event.asset_id == asset_id for event in events)
