"""RW-120-8: Read-only ransomware recovery evidence endpoint."""

from fastapi import APIRouter

from app.services.ransomware_recovery_evidence import assess_recovery_evidence


router = APIRouter()


@router.get("/api/v1/ransomware/recovery/evidence")
def get_recovery_evidence() -> dict:
    """Report recovery evidence availability without operational claims."""
    return assess_recovery_evidence()
