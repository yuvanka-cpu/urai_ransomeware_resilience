from dataclasses import dataclass


LIFECYCLE_STAGES = (
    "initial_access",
    "execution_persistence",
    "privilege_escalation",
    "discovery",
    "lateral_movement",
    "staging",
    "recovery_impairment",
    "encryption_impact",
    "extortion_marker",
    "recovery",
)


@dataclass(frozen=True)
class LifecycleEvent:
    stage: str
    event_family: str
    event_type: str
    asset_id: str
    observable_only: bool = True


def generate_lifecycle(asset_id: str) -> list[LifecycleEvent]:
    return [
        LifecycleEvent(
            stage=stage,
            event_family="synthetic",
            event_type=f"{stage}_observable",
            asset_id=asset_id,
        )
        for stage in LIFECYCLE_STAGES
    ]
