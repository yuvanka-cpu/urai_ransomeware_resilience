from config.ransomware.scenarios.impact_generator import (
    generate_encryption_impact,
)


def test_generates_required_impact_observables():
    events = generate_encryption_impact(
        "energy-blr01-asset-identity-001"
    )

    event_types = {event.event_type for event in events}

    assert event_types == {
        "file_write_spike",
        "file_rename_spike",
        "synthetic_extension_change",
        "entropy_proxy_increase",
        "service_availability_decrease",
    }


def test_impact_events_are_bounded():
    events = generate_encryption_impact(
        "energy-blr01-asset-identity-001"
    )

    assert all(0.0 <= event.value <= 1.0 for event in events)


def test_no_operational_action_is_executed():
    events = generate_encryption_impact(
        "energy-blr01-asset-identity-001"
    )

    assert all(
        event.operational_action_executed is False
        for event in events
    )


def test_no_real_file_target_is_required():
    events = generate_encryption_impact(
        "energy-blr01-asset-identity-001"
    )

    assert all(event.asset_id for event in events)
