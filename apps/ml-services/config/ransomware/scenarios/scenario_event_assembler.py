from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import random

from config.ransomware.scenarios.baseline_generator import generate_baseline
from config.ransomware.scenarios.benign_generator import generate_benign_events
from config.ransomware.scenarios.fault_generator import generate_fault_events
from config.ransomware.scenarios.impact_generator import generate_encryption_impact
from config.ransomware.scenarios.lifecycle_generator import generate_lifecycle
from config.ransomware.scenarios.scenario_registry import FrozenScenario


@dataclass(frozen=True)
class ObservableScenarioEvent:
    scenario_id: str
    scenario_seed: int
    split: str
    sequence_index: int
    event_time: str
    event_family: str
    event_type: str
    asset_id: str
    attributes: dict[str, object]


def _event(
    scenario: FrozenScenario,
    sequence_index: int,
    event_time: datetime,
    event_family: str,
    event_type: str,
    attributes: dict[str, object] | None = None,
    asset_id: str | None = None,
) -> ObservableScenarioEvent:
    return ObservableScenarioEvent(
        scenario_id=scenario.scenario_id,
        scenario_seed=scenario.scenario_seed,
        split=scenario.split,
        sequence_index=sequence_index,
        event_time=event_time.isoformat().replace("+00:00", "Z"),
        event_family=event_family,
        event_type=event_type,
        asset_id=asset_id or scenario.asset_id,
        attributes=attributes or {},
    )


def assemble_scenario_events(scenario: FrozenScenario) -> list[ObservableScenarioEvent]:
    """Build a deterministic observable event sequence for one frozen scenario."""

    start = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
    events: list[ObservableScenarioEvent] = []
    sequence_index = 0
    rng = random.Random(scenario.scenario_seed)
    
    def append(
        event_family: str,
        event_type: str,
        attributes: dict[str, object] | None = None,
        asset_id: str | None = None,
    ) -> None:
        nonlocal sequence_index

        events.append(
            _event(
                scenario=scenario,
                sequence_index=sequence_index,
                event_time=start + timedelta(minutes=sequence_index),
                event_family=event_family,
                event_type=event_type,
                attributes=attributes,
                asset_id=asset_id,
            )
        )
        sequence_index += 1

    variant = scenario.variant

    if variant == "normal":
        for item in generate_baseline([scenario.asset_id], seed=scenario.scenario_seed):
            append(
                item.event_family,
                item.event_type,
                {"value": item.value},
                item.asset_id,
            )

    elif variant == "attack":
        for item in generate_lifecycle(scenario.asset_id):
            append(
                item.event_family,
                item.event_type,
                {"stage": item.stage, "observable_only": item.observable_only},
                item.asset_id,
            )

        for item in generate_encryption_impact(scenario.asset_id):
            observable_value = round(
                max(0.0, min(1.0, item.value + rng.uniform(-0.05, 0.05))),
                3,
            )

            append(
                "file",
                item.event_type,
                {
                     "value": observable_value,
                     "operational_action_executed": item.operational_action_executed,
                 },
                 item.asset_id,
             )

    elif variant == "benign":
        for item in generate_benign_events(scenario.asset_id):
            observable_intensity = round(rng.uniform(0.1, 0.9), 3)

            append(
                "benign_activity",
                 item.scenario_family,
                 {
                     "authorized": item.authorized,
                     "maintenance_context": item.maintenance_context,
                      "activity_intensity": observable_intensity,
                 },
                 item.asset_id,
            )

    elif variant == "fault":
        for item in generate_fault_events(scenario.asset_id):
            observable_severity = round(rng.uniform(0.1, 0.9), 3)

            append(
                "telemetry_quality",
                 item.scenario_family,
                 {
                     "telemetry_quality_issue": item.telemetry_quality_issue,
                     "operational_action_executed": item.operational_action_executed,
                     "degradation_severity": observable_severity,
                 },
                 item.asset_id,
            )

    else:
        raise ValueError(f"Unsupported scenario variant: {variant}")

    return events


def sequence_fingerprint(events: list[ObservableScenarioEvent]) -> str:
    material = [
        {
            "sequence_index": event.sequence_index,
            "event_family": event.event_family,
            "event_type": event.event_type,
            "asset_id": event.asset_id,
            "attributes": event.attributes,
        }
        for event in events
    ]
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def events_to_json(events: list[ObservableScenarioEvent]) -> str:
    return json.dumps(
        [asdict(event) for event in events],
        indent=2,
        sort_keys=True,
      )
