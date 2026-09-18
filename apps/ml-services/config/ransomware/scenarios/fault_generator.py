from dataclasses import dataclass


FAULT_SCENARIO_FAMILIES = (
    "host_outage",
    "network_interruption",
    "disk_pressure",
    "backup_failure",
    "source_loss",
    "reordered_late_events",
    "partial_evidence",
)


@dataclass(frozen=True)
class FaultEvent:
    scenario_family: str
    asset_id: str
    telemetry_quality_issue: bool = False
    operational_action_executed: bool = False


def generate_fault_events(asset_id: str) -> list[FaultEvent]:
    return [
        FaultEvent(
            scenario_family=family,
            asset_id=asset_id,
            telemetry_quality_issue=family
            in {"source_loss", "reordered_late_events", "partial_evidence"},
        )
        for family in FAULT_SCENARIO_FAMILIES
    ]
