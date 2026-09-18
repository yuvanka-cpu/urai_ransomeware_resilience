from dataclasses import dataclass

from config.ransomware.scenarios.use_case_catalogue import (
    ALL_USE_CASES,
    SCENARIO_VARIANTS,
)


@dataclass(frozen=True)
class UseCaseScenario:
    use_case_id: str
    industry: str
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
