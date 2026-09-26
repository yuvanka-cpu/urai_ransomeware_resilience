from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class UseCaseFamily:
    use_case_id: str
    industry: str
    scenario_family: str
    site_types: tuple[str, ...]
    principal_assets: tuple[str, ...]
    observable_evidence: tuple[str, ...]
    protected_boundary_context: tuple[str, ...]


def _load_use_cases(industry: str) -> tuple[UseCaseFamily, ...]:
    path = (
        Path(__file__).resolve().parent.parent
        / industry
        / "use_cases.json"
    )

    payload = json.loads(path.read_text(encoding="utf-8"))

    return tuple(
        UseCaseFamily(
            use_case_id=item["use_case_id"],
            industry=item["industry"],
            scenario_family=item["scenario_family"],
            site_types=tuple(item["site_types"]),
            principal_assets=tuple(item["principal_assets"]),
            observable_evidence=tuple(item["observable_evidence"]),
            protected_boundary_context=tuple(
                item["protected_boundary_context"]
            ),
        )
        for item in payload["use_cases"]
    )


ENERGY_USE_CASES = _load_use_cases("energy")
PETROCHEMICAL_USE_CASES = _load_use_cases("petrochemical")

ALL_USE_CASES = ENERGY_USE_CASES + PETROCHEMICAL_USE_CASES

SCENARIO_VARIANTS = (
    "normal",
    "attack",
    "benign",
    "fault",
)
