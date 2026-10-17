"""RW-120-8: Read-only recovery evidence availability assessment.

This module does not verify backup systems, perform restoration,
calculate resilience scores, or infer operational recoverability.
"""

from typing import Any

TASK_ID = "RW-120-8"

REQUIRED_EVIDENCE = {
    "latest_backup_age": "Verified backup inventory and timestamp",
    "immutable_backup_copy": "Independent backup immutability evidence",
    "last_restore_test": "Verified restore-test record and outcome",
    "configuration_coverage": "Verified configuration coverage assessment",
    "recovery_dependencies": "Verified recovery dependency assessment",
    "resilience_score": "Approved scoring methodology and verified inputs",
}


def assess_recovery_evidence() -> dict[str, Any]:
    """Return explicit unavailability when no verified source is configured."""
    checks = {
        key: {
            "status": "unavailable",
            "evidence_required": description,
            "verified_value": None,
        }
        for key, description in REQUIRED_EVIDENCE.items()
    }

    return {
        "task_id": TASK_ID,
        "status": "unavailable",
        "analysis_type": "recovery_evidence_availability",
        "data_provenance": "not_established",
        "is_operational_recovery_verified": False,
        "real_action_executed": False,
        "human_approval_required": True,
        "physical_safety_determination": "not_determined",
        "checks": checks,
        "backup_readiness": {
            "latest_backup_age_hours": None,
            "immutable_copy_available": None,
            "last_restore_test_age_days": None,
            "configuration_coverage_percent": None,
            "limitations": [
                "No independently verified recovery evidence source is configured.",
                "Synthetic ML features are not proof of backup recoverability.",
            ],
        },
        "resilience_score": None,
        "reason": (
            "Verified backup, restoration, configuration, and dependency "
            "records are unavailable. Recovery readiness cannot be determined."
        ),
    }
