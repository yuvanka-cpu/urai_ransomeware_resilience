from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isclose
from typing import Iterable, Mapping

from config.ransomware.features.window_features import (
    ObservableScenarioEvent,
    extract_window_features,
)
from config.ransomware.shared.validation.event_time_ordering import (
    build_partition_key,
    process_event_time,
)


DEFAULT_FEATURE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class FeatureParityResult:
    compared_fields: int
    mismatches: tuple[str, ...]
    tolerance: float
    replay_event_ids: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.mismatches


def _parse_event_time(event: Mapping[str, object]) -> datetime:
    value = event.get("event_time")
    if not isinstance(value, str):
        raise ValueError("event_time must be a string")

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_observable_events(
    events: Iterable[Mapping[str, object]],
) -> list[ObservableScenarioEvent]:
    observable_events: list[ObservableScenarioEvent] = []

    for index, event in enumerate(events):
        event_time = event.get("event_time")
        event_family = event.get("event_family")
        event_type = event.get("event_type")
        asset_id = event.get("asset_id")
        attributes = event.get("attributes", {})

        if not isinstance(event_time, str):
            raise ValueError("event_time must be a string")
        if not isinstance(event_family, str):
            raise ValueError("event_family must be a string")
        if not isinstance(event_type, str):
            raise ValueError("event_type must be a string")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")
        if not isinstance(attributes, dict):
            raise ValueError("attributes must be a mapping")

        observable_events.append(
            ObservableScenarioEvent(
                scenario_id="feature-parity-replay",
                scenario_seed=0,
                split="parity",
                sequence_index=index,
                event_time=event_time,
                event_family=event_family,
                event_type=event_type,
                asset_id=asset_id,
                attributes=dict(attributes),
            )
        )

    return observable_events


def _filter_partition(
    events: Iterable[Mapping[str, object]],
    partition_key: str,
) -> list[Mapping[str, object]]:
    selected = [
        event
        for event in events
        if build_partition_key(event) == partition_key
    ]

    if not selected:
        raise ValueError(
            f"no events found for partition {partition_key}"
        )

    return selected


def compute_offline_features(
    canonical_events: Iterable[Mapping[str, object]],
    *,
    partition_key: str,
    anchor_time: datetime,
    window_minutes: int,
) -> dict[str, float | int]:
    events = _filter_partition(canonical_events, partition_key)

    ordered = sorted(
        events,
        key=lambda event: (
            _parse_event_time(event),
            str(event["event_id"]),
            str(event["ingest_time"]),
        ),
    )

    return extract_window_features(
        _to_observable_events(ordered),
        anchor_time,
        window_minutes,
    )


def compute_online_features(
    canonical_events: Iterable[Mapping[str, object]],
    *,
    partition_key: str,
    anchor_time: datetime,
    window_minutes: int,
    allowed_lateness: timedelta,
) -> tuple[dict[str, float | int], tuple[str, ...]]:
    result = process_event_time(
        canonical_events,
        allowed_lateness=allowed_lateness,
    )

    try:
        ordered = [
            item.event
            for item in result.events_by_partition[partition_key]
        ]
    except KeyError as exc:
        raise ValueError(
            f"no events found for partition {partition_key}"
        ) from exc

    features = extract_window_features(
        _to_observable_events(ordered),
        anchor_time,
        window_minutes,
    )

    return features, result.replay_event_ids


def compare_feature_rows(
    offline_features: Mapping[str, float | int],
    online_features: Mapping[str, float | int],
    *,
    tolerance: float = DEFAULT_FEATURE_TOLERANCE,
) -> FeatureParityResult:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")

    fields = sorted(set(offline_features) | set(online_features))
    mismatches: list[str] = []

    for field in fields:
        if field not in offline_features:
            mismatches.append(f"{field}: missing_offline")
            continue

        if field not in online_features:
            mismatches.append(f"{field}: missing_online")
            continue

        offline_value = offline_features[field]
        online_value = online_features[field]

        if isinstance(offline_value, float) or isinstance(
            online_value,
            float,
        ):
            if not isclose(
                float(offline_value),
                float(online_value),
                rel_tol=tolerance,
                abs_tol=tolerance,
            ):
                mismatches.append(
                    f"{field}: offline={offline_value} online={online_value}"
                )
        elif offline_value != online_value:
            mismatches.append(
                f"{field}: offline={offline_value} online={online_value}"
            )

    return FeatureParityResult(
        compared_fields=len(fields),
        mismatches=tuple(mismatches),
        tolerance=tolerance,
        replay_event_ids=(),
    )
