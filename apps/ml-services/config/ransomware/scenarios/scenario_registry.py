from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from config.ransomware.scenarios.use_case_variants import (
    UseCaseScenario,
    generate_use_case_scenarios,
)


SPLITS = (
    "train",
    "validation",
    "calibration",
    "test",
    "untouched_holdout",
)

DEFAULT_SEED = 20260921


@dataclass(frozen=True)
class FrozenScenario:
    scenario_id: str
    scenario_seed: int
    use_case_id: str
    industry: str
    variant: str
    asset_id: str
    protected_boundary: str
    split: str


def _scenario_seed(scenario: UseCaseScenario, base_seed: int) -> int:
    material = (
        f"{base_seed}|{scenario.use_case_id}|"
        f"{scenario.industry}|{scenario.variant}|{scenario.asset_id}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _scenario_id(scenario: UseCaseScenario, scenario_seed: int) -> str:
    material = (
        f"{scenario.use_case_id}|{scenario.industry}|"
        f"{scenario.variant}|{scenario.asset_id}|{scenario_seed}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]

    return f"rw-{scenario.variant}-{digest}"


def build_frozen_scenarios(
    asset_ids: list[str],
    base_seed: int = DEFAULT_SEED,
) -> list[FrozenScenario]:
    """Build deterministic scenario identities without modifying event generators."""
    scenarios: list[FrozenScenario] = []

    generated: list[UseCaseScenario] = []

    for asset_id in asset_ids:
        generated.extend(generate_use_case_scenarios(asset_id))

    for scenario in generated:
        seed = _scenario_seed(scenario, base_seed)
        scenario_id = _scenario_id(scenario, seed)

        # Deterministically assign each scenario to one of the five
        # required evaluation splits.
        split_material = (
            f"{scenario_id}|{seed}|split"
        )
        split_digest = hashlib.sha256(
            split_material.encode("utf-8")
        ).hexdigest()

        split_index = int(split_digest[:8], 16) % len(SPLITS)
        split = SPLITS[split_index]

        scenarios.append(
            FrozenScenario(
                scenario_id=scenario_id,
                scenario_seed=seed,
                use_case_id=scenario.use_case_id,
                industry=scenario.industry,
                variant=scenario.variant,
                asset_id=scenario.asset_id,
                protected_boundary=scenario.protected_boundary,
                split=split,
            )
        )

    return sorted(
        scenarios,
        key=lambda item: item.scenario_id,
    )


def build_split_assignment_manifest(
    asset_ids: list[str],
    base_seed: int = DEFAULT_SEED,
) -> dict:
    frozen = build_frozen_scenarios(
        asset_ids,
        base_seed=base_seed,
    )

    assignments = [asdict(item) for item in frozen]

    return {
        "manifest_version": "1.0",
        "manifest_type": "split_assignment",
        "base_seed": base_seed,
        "splits": list(SPLITS),
        "scenario_count": len(assignments),
        "assignments": assignments,
    }


def manifest_to_json(manifest: dict) -> str:
    return json.dumps(
        manifest,
        indent=2,
        sort_keys=True,
    )