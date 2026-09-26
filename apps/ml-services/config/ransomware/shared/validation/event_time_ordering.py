from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Iterable, Mapping


@dataclass(frozen=True)
class OrderedEvent:
    event: dict[str, object]
    partition_key: str
    event_time: datetime
    ingest_time: datetime
    late: bool


@dataclass(frozen=True)
class EventTimeProcessingResult:
    events_by_partition: dict[str, tuple[OrderedEvent, ...]]
    watermarks: dict[str, datetime]
    replay_event_ids: tuple[str, ...]
    late_event_ids: tuple[str, ...]


def _parse_utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: timestamp must be a string")

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            f"{field_name}: invalid timestamp"
        ) from exc

    if (
        parsed.utcoffset() is None
        or parsed.utcoffset() != timezone.utc.utcoffset(parsed)
        or not value.endswith("Z")
    ):
        raise ValueError(
            f"{field_name}: timestamp must be canonical UTC"
        )

    return parsed.astimezone(timezone.utc)


def build_partition_key(event: Mapping[str, object]) -> str:
    site_id = event.get("site_id")
    asset_id = event.get("asset_id")

    if not isinstance(site_id, str) or not isinstance(asset_id, str):
        raise ValueError(
            "partition key requires string site_id and asset_id"
        )

    return f"{site_id}+{asset_id}"


def _event_fingerprint(event: Mapping[str, object]) -> str:
    return json.dumps(
        dict(event),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def process_event_time(
    events: Iterable[Mapping[str, object]],
    *,
    allowed_lateness: timedelta,
) -> EventTimeProcessingResult:
    if allowed_lateness < timedelta(0):
        raise ValueError("allowed_lateness must be non-negative")

    unique_events: dict[str, dict[str, object]] = {}
    fingerprints: dict[str, str] = {}
    replay_event_ids: list[str] = []

    for source_event in events:
        event = dict(source_event)
        event_id = event.get("event_id")

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id must be a non-empty string")

        fingerprint = _event_fingerprint(event)

        if event_id in fingerprints:
            if fingerprints[event_id] != fingerprint:
                raise ValueError(
                    f"conflicting replay detected for event_id={event_id}"
                )

            replay_event_ids.append(event_id)
            continue

        fingerprints[event_id] = fingerprint
        unique_events[event_id] = event

    arrival_order = sorted(
        unique_events.values(),
        key=lambda event: (
            _parse_utc(event["ingest_time"], "ingest_time"),
            str(event["event_id"]),
        ),
    )

    max_event_time_seen: dict[str, datetime] = {}
    watermarks: dict[str, datetime] = {}
    events_by_partition: dict[str, list[OrderedEvent]] = defaultdict(list)
    late_event_ids: list[str] = []

    for event in arrival_order:
        event_time = _parse_utc(event["event_time"], "event_time")
        ingest_time = _parse_utc(event["ingest_time"], "ingest_time")
        partition_key = build_partition_key(event)

        previous_max = max_event_time_seen.get(partition_key)
        current_max = (
            event_time
            if previous_max is None
            else max(previous_max, event_time)
        )

        max_event_time_seen[partition_key] = current_max

        watermark = current_max - allowed_lateness
        watermarks[partition_key] = watermark

        is_late = event_time < watermark

        if is_late:
            late_event_ids.append(str(event["event_id"]))

        events_by_partition[partition_key].append(
            OrderedEvent(
                event=event,
                partition_key=partition_key,
                event_time=event_time,
                ingest_time=ingest_time,
                late=is_late,
            )
        )

    ordered_partitions = {
        partition_key: tuple(
            sorted(
                partition_events,
                key=lambda item: (
                    item.event_time,
                    str(item.event["event_id"]),
                    item.ingest_time,
                ),
            )
        )
        for partition_key, partition_events in events_by_partition.items()
    }

    return EventTimeProcessingResult(
        events_by_partition=ordered_partitions,
        watermarks=dict(watermarks),
        replay_event_ids=tuple(replay_event_ids),
        late_event_ids=tuple(late_event_ids),
    )
