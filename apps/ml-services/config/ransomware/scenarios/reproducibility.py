from dataclasses import asdict

from config.ransomware.scenarios.baseline_generator import generate_baseline


def generate_reproducible_baseline(
    asset_ids: list[str],
    seed: int,
) -> list[dict]:
    events = generate_baseline(asset_ids, seed=seed)

    return [asdict(event) for event in events]
