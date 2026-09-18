from dataclasses import dataclass


BENIGN_SCENARIO_FAMILIES = (
    "patching",
    "deployment",
    "bulk_copy",
    "compression",
    "backup",
    "restore_test",
    "approved_administration",
    "vendor_support",
    "relay_configuration_work",
    "turnaround_work",
    "failover",
    "historian_replay",
    "campaign_changes",
)


@dataclass(frozen=True)
class BenignEvent:
    scenario_family: str
    asset_id: str
    authorized: bool = True
    maintenance_context: bool = True


def generate_benign_events(asset_id: str) -> list[BenignEvent]:
    return [
        BenignEvent(
            scenario_family=family,
            asset_id=asset_id,
        )
        for family in BENIGN_SCENARIO_FAMILIES
    ]
