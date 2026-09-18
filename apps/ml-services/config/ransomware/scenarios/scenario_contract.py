from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScenarioConfig:
    scenario_id: str
    seed: int
    industry: str
    site: str
    asset_set: list[str]
    lifecycle_timing: dict[str, int]
    event_family_parameters: dict[str, dict[str, Any]]
    intended_labels: dict[str, Any] = field(default_factory=dict)
