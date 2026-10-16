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

# Cycle-2 deterministic sector/variant stratification.
# Each sector has 10 scenarios for each variant in the current
# synthetic scenario pool. The quotas guarantee class diversity
# in calibration and positive coverage in the final holdout.
SPLIT_QUOTAS = {
    "energy": {
        "attack": {
            "train": 2,
            "validation": 2,
            "calibration": 2,
            "test": 2,
            "untouched_holdout": 2,
        },
        "benign": {
            "train": 2,
            "validation": 2,
            "calibration": 1,
            "test": 2,
            "untouched_holdout": 3,
        },
        "fault": {
            "train": 2,
            "validation": 2,
            "calibration": 1,
            "test": 2,
            "untouched_holdout": 3,
        },
        "normal": {
            "train": 3,
            "validation": 3,
            "calibration": 1,
            "test": 1,
            "untouched_holdout": 2,
        },
    },
    "petrochemical": {
        "attack": {
            "train": 2,
            "validation": 2,
            "calibration": 2,
            "test": 2,
            "untouched_holdout": 2,
        },
        "benign": {
            "train": 2,
            "validation": 2,
            "calibration": 1,
            "test": 2,
            "untouched_holdout": 3,
        },
        "fault": {
            "train": 2,
            "validation": 2,
            "calibration": 1,
            "test": 2,
            "untouched_holdout": 3,
        },
        "normal": {
            "train": 3,
            "validation": 3,
            "calibration": 1,
            "test": 1,
            "untouched_holdout": 2,
        },
    },
}


@dataclass(frozen=True)
class FrozenScenario:
    scenario_id: str
    scenario_seed: int
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

    prepared = []

    for scenario in generated:
        seed = _scenario_seed(scenario, base_seed)
        scenario_id = _scenario_id(scenario, seed)
        prepared.append((scenario, seed, scenario_id))

    split_lookup = {}

    grouped = {}
    for scenario, seed, scenario_id in prepared:
        key = (scenario.industry, scenario.variant)
        grouped.setdefault(key, []).append(
            (scenario, seed, scenario_id)
        )

    for (industry, variant), group in grouped.items():
        if industry not in SPLIT_QUOTAS:
            raise ValueError(
                f"Missing split quotas for industry: {industry}"
            )

        if variant not in SPLIT_QUOTAS[industry]:
            raise ValueError(
                f"Missing split quotas for {industry}/{variant}"
            )

        quotas = SPLIT_QUOTAS[industry][variant]
        expected = sum(quotas.values())

        if len(group) != expected:
            raise ValueError(
                f"Expected {expected} scenarios for "
                f"{industry}/{variant}, found {len(group)}"
            )

        ranked = sorted(
            group,
            key=lambda item: hashlib.sha256(
                f"{base_seed}|{item[2]}|cycle-2-stratified-v1800".encode("utf-8")
            ).hexdigest(),
        )

        offset = 0

        for split in SPLITS:
            count = quotas[split]

            for item in ranked[offset:offset + count]:
                split_lookup[item[2]] = split

            offset += count

    for scenario, seed, scenario_id in prepared:
        split = split_lookup[scenario_id]

        scenarios.append(
            FrozenScenario(
                scenario_id=scenario_id,
                scenario_seed=seed,
                use_case_id=scenario.use_case_id,
                industry=scenario.industry,
                scenario_family=scenario.scenario_family,
                site_types=scenario.site_types,
                principal_assets=scenario.principal_assets,
                observable_evidence=scenario.observable_evidence,
                protected_boundary_context=scenario.protected_boundary_context,
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
