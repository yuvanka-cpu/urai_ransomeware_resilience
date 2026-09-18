from dataclasses import dataclass
import random


@dataclass(frozen=True)
class BaselineEvent:
    event_family: str
    event_type: str
    asset_id: str
    value: float


EVENT_FAMILIES = (
    "identity",
    "endpoint",
    "file",
    "network",
    "backup",
    "service_health",
)


def generate_baseline(
    asset_ids: list[str],
    seed: int = 42,
    events_per_asset: int = 6,
) -> list[BaselineEvent]:
    rng = random.Random(seed)
    events = []

    for asset_id in asset_ids:
        for index in range(events_per_asset):
            family = EVENT_FAMILIES[index % len(EVENT_FAMILIES)]

            events.append(
                BaselineEvent(
                    event_family=family,
                    event_type=f"{family}_baseline",
                    asset_id=asset_id,
                    value=round(rng.uniform(0.1, 1.0), 3),
                )
            )

    return events
