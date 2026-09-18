from config.ransomware.scenarios.reproducibility import (
    generate_reproducible_baseline,
)


ASSETS = [
    "energy-blr01-asset-identity-001",
    "energy-blr01-asset-engineering-001",
]


def test_same_seed_produces_identical_output():
    first = generate_reproducible_baseline(ASSETS, seed=42)
    second = generate_reproducible_baseline(ASSETS, seed=42)

    assert first == second


def test_different_seeds_produce_different_output():
    first = generate_reproducible_baseline(ASSETS, seed=42)
    second = generate_reproducible_baseline(ASSETS, seed=99)

    assert first != second


def test_output_structure_is_stable():
    events = generate_reproducible_baseline(ASSETS, seed=42)

    assert events
    assert all(
        set(event) == {
            "event_family",
            "event_type",
            "asset_id",
            "value",
        }
        for event in events
    )


def test_same_seed_preserves_row_count():
    first = generate_reproducible_baseline(ASSETS, seed=42)
    second = generate_reproducible_baseline(ASSETS, seed=42)

    assert len(first) == len(second)
