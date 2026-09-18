from dataclasses import dataclass


@dataclass(frozen=True)
class ImpactEvent:
    event_type: str
    asset_id: str
    value: float
    operational_action_executed: bool = False


def generate_encryption_impact(asset_id: str) -> list[ImpactEvent]:
    return [
        ImpactEvent("file_write_spike", asset_id, 0.85),
        ImpactEvent("file_rename_spike", asset_id, 0.80),
        ImpactEvent("synthetic_extension_change", asset_id, 0.90),
        ImpactEvent("entropy_proxy_increase", asset_id, 0.95),
        ImpactEvent("service_availability_decrease", asset_id, 0.35),
    ]
