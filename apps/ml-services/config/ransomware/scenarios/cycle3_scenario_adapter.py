"""Cycle 3 adapter for sector-compatible, asset-grouped scenarios.

Creates in-memory FrozenScenario objects for development and calibration.
Does not modify the historical registry, holdout, or promoted models.
"""

from dataclasses import dataclass

from config.ransomware.scenarios.cycle3_split_assignment import (
    DEFAULT_SEED,
    build_cycle3_split_manifest,
)
from config.ransomware.scenarios.scenario_registry import (
    FrozenScenario,
    _scenario_id,
    _scenario_seed,
)
from config.ransomware.scenarios.sector_compatible_cycle3 import (
    build_sector_compatible_scenarios,
)


@dataclass(frozen=True)
class Cycle3AdaptedBatch:
    version: str
    seed: int
    scenarios: tuple[FrozenScenario, ...]


def build_cycle3_adapted_scenarios(
    seed: int = DEFAULT_SEED,
) -> Cycle3AdaptedBatch:
    """Adapt Cycle 3 scenarios without changing historical split logic."""

    manifest = build_cycle3_split_manifest(seed=seed)

    split_lookup = {}

    for assignment in manifest.assignments:
        key = (
            assignment.sector,
            assignment.asset_id,
            assignment.use_case_id,
            assignment.variant,
        )

        if key in split_lookup:
            raise ValueError(f"Duplicate split assignment: {key}")

        split_lookup[key] = assignment.split

    adapted = []
    used_keys = set()
    scenario_ids = set()

    for sector in ("energy", "petrochemical"):
        batch = build_sector_compatible_scenarios(sector)

        for scenario in batch.scenarios:
            key = (
                scenario.industry,
                scenario.asset_id,
                scenario.use_case_id,
                scenario.variant,
            )

            if key not in split_lookup:
                raise ValueError(f"Missing split assignment: {key}")

            if key in used_keys:
                raise ValueError(f"Duplicate scenario identity: {key}")

            used_keys.add(key)

            scenario_seed = _scenario_seed(scenario, seed)
            scenario_id = _scenario_id(scenario, scenario_seed)

            if scenario_id in scenario_ids:
                raise ValueError(f"Duplicate scenario ID: {scenario_id}")

            scenario_ids.add(scenario_id)

            adapted.append(
                FrozenScenario(
                    scenario_id=scenario_id,
                    scenario_seed=scenario_seed,
                    use_case_id=scenario.use_case_id,
                    industry=scenario.industry,
                    scenario_family=scenario.scenario_family,
                    site_types=scenario.site_types,
                    principal_assets=scenario.principal_assets,
                    observable_evidence=scenario.observable_evidence,
                    protected_boundary_context=(
                        scenario.protected_boundary_context
                    ),
                    variant=scenario.variant,
                    asset_id=scenario.asset_id,
                    protected_boundary=scenario.protected_boundary,
                    split=split_lookup[key],
                )
            )

    if used_keys != set(split_lookup):
        raise ValueError("Unconsumed Cycle 3 split assignments")

    if len(adapted) != 420:
        raise ValueError(
            f"Unexpected Cycle 3 scenario count: {len(adapted)}"
        )

    return Cycle3AdaptedBatch(
        version=manifest.version,
        seed=seed,
        scenarios=tuple(
            sorted(adapted, key=lambda item: item.scenario_id)
        ),
    )
