from config.ransomware.scenarios.baseline_generator import generate_baseline


ASSETS = [
    "energy-blr01-asset-identity-001",
    "energy-blr01-asset-vpn-001",
]


def test_baseline_covers_required_event_families():
    events = generate_baseline(ASSETS, seed=42)

    families = {event.event_family for event in events}

    assert families == {
        "identity",
        "endpoint",
        "file",
        "network",
        "backup",
        "service_health",
    }


def test_baseline_is_deterministic():
    first = generate_baseline(ASSETS, seed=42)
    second = generate_baseline(ASSETS, seed=42)

    assert first == second


def test_baseline_changes_with_seed():
    first = generate_baseline(ASSETS, seed=42)
    second = generate_baseline(ASSETS, seed=99)

    assert first != second


def test_baseline_values_are_bounded():
    events = generate_baseline(ASSETS, seed=42)

    assert all(0.1 <= event.value <= 1.0 for event in events)
