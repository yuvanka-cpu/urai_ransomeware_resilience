from typing import Any


def enforce_safety_invariants(result: dict[str, Any]) -> dict[str, Any]:
    result["human_approval_required"] = True
    result["real_action_executed"] = False

    operational_impact = result.get("operational_dependency_impact", [])

    for item in operational_impact:
        item["physical_safety_determination"] = "not_determined"
        item["operational_state_claimed"] = False

    warnings = result.setdefault("warnings", [])

    required_warning = (
        "Synthetic defensive analysis only; physical safety is not determined."
    )

    if required_warning not in warnings:
        warnings.append(required_warning)

    return result
