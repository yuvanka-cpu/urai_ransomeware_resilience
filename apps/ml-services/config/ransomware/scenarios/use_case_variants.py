from dataclasses import dataclass

from config.ransomware.scenarios.use_case_catalogue import (
    ALL_USE_CASES,
    SCENARIO_VARIANTS,
)


@dataclass(frozen=True)
class UseCaseScenario:
    use_case_id: str
    industry: str
    scenario_family: str
    site_types: tuple[str, ...]
    principal_assets: tuple[str, ...]
    observable_evidence: tuple[str, ...]
    protected_boundary_context: tuple[str, ...]
    variant: str
    asset_id: str
    protected_boundary: str


def generate_use_case_scenarios(
    asset_id: str,
) -> list[UseCaseScenario]:
    scenarios = []

    for use_case in ALL_USE_CASES:
        for variant in SCENARIO_VARIANTS:
            scenarios.append(
                UseCaseScenario(
                    use_case_id=use_case.use_case_id,
                    industry=use_case.industry,
                    scenario_family=use_case.scenario_family,
                    site_types=use_case.site_types,
                    principal_assets=use_case.principal_assets,
                    observable_evidence=use_case.observable_evidence,
                    protected_boundary_context=use_case.protected_boundary_context,
                    variant=variant,
                    asset_id=asset_id,
                    protected_boundary=(
                        "protection_safety"
                        if use_case.industry == "energy"
                        else "safety_system"
                    ),
                )
            )

    return scenarios
