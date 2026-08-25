from typing import Literal
from pydantic import BaseModel
from app.schemas.enums import Decision, IncidentStage, Severity
class RansomwareResponse(BaseModel):
    use_case:str
    industry:str
    site_id:str
    site_type:str
    scenario_id:str

    decision: Decision
    incident_stage: IncidentStage
    confidence: float
    severity: Severity
    resilience_score: float

    affected_assets: list[str]
    suspected_assets: list[str]
    critical_services_at_risk: list[str]
    affected_zones: list[str]
    protected_boundaries: list[str]
    operational_dependency_impact: list[str]

    propagation_path: list[str]
    evidence_layers: list[str]
    triggered_rules: list[str]
    timeline: list[str]

    backup_readiness: dict
    explanations: list[str]
    recommended_actions: list[str]

    human_approval_required: Literal[True]
    real_action_executed: Literal[False]

    artifact_provenance: list[str]
    data_provenance: str
    warnings: list[str]

    request_id: str
    runtime_state: str