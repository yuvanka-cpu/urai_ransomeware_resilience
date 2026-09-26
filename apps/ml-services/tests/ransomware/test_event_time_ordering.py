from datetime import datetime, timedelta, timezone

import pytest

from config.ransomware.shared.validation.event_time_ordering import (
    build_partition_key,
    process_event_time,
)


def _event(
    event_id: str,
    event_time: str,
    ingest_time: str,
    site_id: str = "energy-blr01",
    asset_id: str = "energy-blr01-asset-scada-support-001",
):
    return {
        "event_id": event_id,
        "event_time": event_time,
        "ingest_time": ingest_time,
        "site_id": site_id,
        "asset_id": asset_id,
    }


def test_rw0608_partition_key_is_site_and_asset():
    event = _event(
        "evt-001",
        "2026-01-01T06:00:00Z",
        "2026-01-01T06:00:01Z",
    )

    assert (
        build_partition_key(event)
        == "energy-blr01+energy-blr01-asset-scada-support-001"
    )


def test_rw0608_event_time_order_overrides_ingest_order():
    events = [
        _event(
            "evt-002",
            "2026-01-01T06:02:00Z",
            "2026-01-01T06:00:02Z",
        ),
        _event(
            "evt-001",
            "2026-01-01T06:01:00Z",
            "2026-01-01T06:00:01Z",
        ),
    ]

    result = process_event_time(
        events,
        allowed_lateness=timedelta(minutes=5),
    )

    ordered_ids = [
        item.event["event_id"]
        for item in result.events_by_partition[
            "energy-blr01+energy-blr01-asset-scada-support-001"
        ]
    ]

    assert ordered_ids == ["evt-001", "evt-002"]


def test_rw0608_watermark_and_bounded_lateness():
    events = [
        _event(
            "evt-001",
            "2026-01-01T06:10:00Z",
            "2026-01-01T06:10:01Z",
        ),
        _event(
            "evt-002",
            "2026-01-01T06:04:00Z",
            "2026-01-01T06:11:01Z",
        ),
        _event(
            "evt-003",
            "2026-01-01T06:05:00Z",
            "2026-01-01T06:12:01Z",
        ),
    ]

    result = process_event_time(
        events,
        allowed_lateness=timedelta(minutes=5),
    )

    watermark = result.watermarks[
        "energy-blr01+energy-blr01-asset-scada-support-001"
    ]

    assert watermark == datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )
    assert result.late_event_ids == ("evt-002",)


def test_rw0608_replay_is_deduplicated():
    event = _event(
        "evt-001",
        "2026-01-01T06:00:00Z",
        "2026-01-01T06:00:01Z",
    )

    result = process_event_time(
        [event, dict(event)],
        allowed_lateness=timedelta(minutes=5),
    )

    partition = (
        "energy-blr01+energy-blr01-asset-scada-support-001"
    )

    assert len(result.events_by_partition[partition]) == 1
    assert result.replay_event_ids == ("evt-001",)


def test_rw0608_conflicting_replay_is_rejected():
    first = _event(
        "evt-001",
        "2026-01-01T06:00:00Z",
        "2026-01-01T06:00:01Z",
    )
    conflicting = dict(first)
    conflicting["event_time"] = "2026-01-01T06:01:00Z"

    with pytest.raises(ValueError, match="conflicting replay"):
        process_event_time(
            [first, conflicting],
            allowed_lateness=timedelta(minutes=5),
        )


def test_rw0608_partition_watermarks_are_independent():
    events = [
        _event(
            "evt-001",
            "2026-01-01T06:10:00Z",
            "2026-01-01T06:10:01Z",
        ),
        _event(
            "evt-002",
            "2026-01-01T06:03:00Z",
            "2026-01-01T06:10:02Z",
            asset_id="energy-blr01-asset-historian-001",
        ),
    ]

    result = process_event_time(
        events,
        allowed_lateness=timedelta(minutes=5),
    )

    assert result.watermarks[
        "energy-blr01+energy-blr01-asset-scada-support-001"
    ] == datetime(
        2026,
        1,
        1,
        6,
        5,
        tzinfo=timezone.utc,
    )

    assert result.watermarks[
        "energy-blr01+energy-blr01-asset-historian-001"
    ] == datetime(
        2026,
        1,
        1,
        5,
        58,
        tzinfo=timezone.utc,
    )
