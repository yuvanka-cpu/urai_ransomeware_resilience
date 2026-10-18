"""Cycle 3 sector-compatible synthetic scenario construction.

Development-only scenario preparation. Historical scenario registries,
split assignments, frozen holdouts and promoted models are untouched.
"""

from dataclasses import dataclass

from config.ransomware.asset_compatibility_cycle3 import (
    validate_sector_asset,
)
from config.ransomware.graph_propagation import load_sector_graph
from config.ransomware.scenarios.use_case_variants import (
    UseCaseScenario,
    generate_use_case_scenarios,
)


SUPPORTED_SECTORS = ("energy", "petrochemical")


@dataclass(frozen=True)
class Cycle3ScenarioBatch:
    sector: str
    asset_ids: tuple[str, ...]
    scenarios: tuple[UseCaseScenario, ...]


def build_sector_compatible_scenarios(
    sector: str,
    asset_ids: list[str] | tuple[str, ...] | None = None,
) -> Cycle3ScenarioBatch:
    """Construct sector-matched scenarios without altering asset identity."""

    if sector not in SUPPORTED_SECTORS:
        raise ValueError("Unsupported sector")

    graph = load_sector_graph(sector)

    if asset_ids is None:
        selected_assets = tuple(sorted(graph.assets))
    else:
        if not isinstance(asset_ids, (list, tuple)) or not asset_ids:
            raise ValueError("asset_ids must be a non-empty list or tuple")

        selected_assets = tuple(asset_ids)

    if len(set(selected_assets)) != len(selected_assets):
        raise ValueError("Duplicate asset IDs are not permitted")

    for asset_id in selected_assets:
        result = validate_sector_asset(sector, asset_id)

        if not result.compatible:
            raise ValueError(
                f"Incompatible asset for {sector}: "
                f"{asset_id} ({result.status})"
            )

    scenarios = []

    for asset_id in selected_assets:
        generated = generate_use_case_scenarios(asset_id)

        for scenario in generated:
            if scenario.industry != sector:
                continue

            result = validate_sector_asset(
                scenario.industry,
                scenario.asset_id,
            )

            if not result.compatible:
                raise ValueError(
                    f"Generated incompatible scenario: "
                    f"{scenario.use_case_id}/{scenario.asset_id}"
                )

            scenarios.append(scenario)

    if not scenarios:
        raise ValueError("No sector-compatible scenarios generated")

    return Cycle3ScenarioBatch(
        sector=sector,
        asset_ids=selected_assets,
        scenarios=tuple(scenarios),
    )
