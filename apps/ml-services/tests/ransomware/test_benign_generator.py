from config.ransomware.scenarios.benign_generator import (
    BENIGN_SCENARIO_FAMILIES,
    generate_benign_events,
)


def test_contains_all_required_benign_families():
    events = generate_benign_events(
        "energy-blr01-asset-engineering-001"
    )

    assert {event.scenario_family for event in events} == set(
        BENIGN_SCENARIO_FAMILIES
    )


def test_benign_events_have_authorization_context():
    events = generate_benign_events(
        "petrochemical-mng01-asset-engineering-001"
    )

    assert all(event.authorized for event in events)
    assert all(event.maintenance_context for event in events)


def test_benign_events_preserve_asset_identity():
    asset_id = "energy-blr01-asset-engineering-001"

    events = generate_benign_events(asset_id)

    assert all(event.asset_id == asset_id for event in events)


def test_benign_generator_is_non_operational():
    events = generate_benign_events(
        "energy-blr01-asset-engineering-001"
    )

    assert all(event.authorized for event in events)
