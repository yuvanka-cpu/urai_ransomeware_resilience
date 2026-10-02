from app.schemas.requests import RansomwareRequest
from app.policies.ransomware_scenario_registry import PERMITTED_SYNTHETIC_SCENARIOS


def validate_synthetic_request(request: RansomwareRequest) -> None:
    if request.scenario_id not in PERMITTED_SYNTHETIC_SCENARIOS:
        raise ValueError(
            f"synthetic scenario is not permitted: {request.scenario_id}"
        )

    if request.industry.value == "energy" and request.site_type.value not in {
        "control_centre",
        "substation",
    }:
        raise ValueError("site_type is not permitted for energy")

    if request.industry.value == "petrochemical" and request.site_type.value not in {
        "refinery",
        "petrochemical_complex",
    }:
        raise ValueError("site_type is not permitted for petrochemical")
