"""Validated observable-event construction for Cycle 3.

Development-only adapter. Does not generate complete timelines,
modify historical datasets, train models, or execute industrial actions.
"""

from datetime import datetime, timezone
from typing import Literal

from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)
from config.ransomware.scenarios.cycle3_evidence_mapping_gate import (
    require_cycle3_evidence_mapping,
)
from config.ransomware.scenarios.cycle3_measurement_value_gate import (
    require_cycle3_measurement_value,
)
from config.ransomware.scenarios.cycle3_shared_evidence_vocabulary import (
    get_cycle3_evidence_definition,
)


ALLOWED_SPLITS = frozenset({"development", "calibration"})


def build_cycle3_validated_event(
    *,
    scenario_id: str,
    scenario_seed: int,
    split: Literal["development", "calibration"],
    sequence_index: int,
    event_time: datetime,
    asset_id: str,
    event_type: str,
    measured_value: object,
) -> ObservableScenarioEvent:
    """Construct one validated, model-facing observable event."""

    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ValueError("Invalid scenario_id")

    if type(scenario_seed) is not int or scenario_seed < 0:
        raise ValueError("Invalid scenario_seed")

    if split not in ALLOWED_SPLITS:
        raise ValueError("Invalid Cycle 3 split")

    if type(sequence_index) is not int or sequence_index < 0:
        raise ValueError("Invalid sequence_index")

    if not isinstance(event_time, datetime):
        raise ValueError("Invalid event_time")

    if event_time.tzinfo is None or event_time.utcoffset() is None:
        raise ValueError("Event timestamp must be timezone-aware")

    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("Invalid asset_id")

    mapping = require_cycle3_evidence_mapping(event_type)

    value = require_cycle3_measurement_value(
        event_type,
        measured_value,
    )

    definition = get_cycle3_evidence_definition(event_type)

    if mapping.attribute_name is None:
        raise ValueError("Missing validated attribute mapping")

    timestamp = event_time.astimezone(timezone.utc)

    return ObservableScenarioEvent(
        scenario_id=scenario_id,
        scenario_seed=scenario_seed,
        split=split,
        sequence_index=sequence_index,
        event_time=timestamp.isoformat().replace("+00:00", "Z"),
        event_family=definition.evidence_domain,
        event_type=event_type,
        asset_id=asset_id,
        attributes={
            mapping.attribute_name: value,
        },
    )
