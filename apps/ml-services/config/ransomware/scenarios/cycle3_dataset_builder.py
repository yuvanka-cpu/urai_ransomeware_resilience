"""Cycle 3 in-memory, contract-validated synthetic feature dataset.

Development and calibration only. No holdout creation, file writes,
model training, or modification of historical artifacts.
"""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from config.ransomware.features.window_features import (
    extract_window_features,
)
from config.ransomware.rw1002_feature_contract import (
    EXPECTED_FEATURE_COUNT,
    validate_feature_row,
)
from config.ransomware.scenarios.cycle3_scenario_adapter import (
    build_cycle3_adapted_scenarios,
)
from config.ransomware.scenarios.cycle3_split_assignment import (
    DEFAULT_SEED,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)
from config.ransomware.shared.validation.feature_leakage_guard import (
    validate_deployed_features,
)


WINDOWS = (1, 5, 15)
ALLOWED_SPLITS = frozenset({"development", "calibration"})


@dataclass(frozen=True)
class Cycle3DatasetRow:
    scenario_id: str
    sector: str
    asset_id: str
    split: str
    use_case_id: str
    variant: str
    window_minutes: int
    features: tuple[tuple[str, float | int], ...]


@dataclass(frozen=True)
class Cycle3Dataset:
    version: str
    seed: int
    feature_names: tuple[str, ...]
    rows: tuple[Cycle3DatasetRow, ...]


def build_cycle3_dataset(
    seed: int = DEFAULT_SEED,
) -> Cycle3Dataset:
    """Build validated features without mixing metadata into model inputs."""

    batch = build_cycle3_adapted_scenarios(seed=seed)

    rows = []
    identities = set()
    assets_by_split = {
        "development": set(),
        "calibration": set(),
    }
    canonical_names = None

    for scenario in batch.scenarios:
        if scenario.split not in ALLOWED_SPLITS:
            raise ValueError("Unexpected Cycle 3 split")

        assets_by_split[scenario.split].add(scenario.asset_id)

        events = assemble_scenario_events(scenario)

        if not events:
            raise ValueError(
                f"No events for scenario {scenario.scenario_id}"
            )

        anchor = max(
            datetime.fromisoformat(
                event.event_time.replace("Z", "+00:00")
            )
            for event in events
        )

        for minutes in WINDOWS:
            identity = (scenario.scenario_id, minutes)

            if identity in identities:
                raise ValueError(
                    f"Duplicate scenario/window identity: {identity}"
                )

            identities.add(identity)

            features = extract_window_features(
                events,
                anchor,
                minutes,
            )

            validate_feature_row(features)
            validate_deployed_features(list(features))

            names = tuple(sorted(features))

            if len(names) != EXPECTED_FEATURE_COUNT:
                raise ValueError("Unexpected feature count")

            if canonical_names is None:
                canonical_names = names
            elif names != canonical_names:
                raise ValueError("Feature ordering mismatch")

            for name, value in features.items():
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                ):
                    raise ValueError(
                        f"Invalid feature value: {name}={value!r}"
                    )

            rows.append(
                Cycle3DatasetRow(
                    scenario_id=scenario.scenario_id,
                    sector=scenario.industry,
                    asset_id=scenario.asset_id,
                    split=scenario.split,
                    use_case_id=scenario.use_case_id,
                    variant=scenario.variant,
                    window_minutes=minutes,
                    features=tuple(
                        (name, features[name])
                        for name in names
                    ),
                )
            )

    if not assets_by_split["development"].isdisjoint(
        assets_by_split["calibration"]
    ):
        raise ValueError("Asset leakage across dataset splits")

    if len(rows) != 1260:
        raise ValueError(
            f"Unexpected Cycle 3 dataset size: {len(rows)}"
        )

    if canonical_names is None:
        raise ValueError("No canonical feature names")

    return Cycle3Dataset(
        version=batch.version,
        seed=seed,
        feature_names=canonical_names,
        rows=tuple(rows),
    )
