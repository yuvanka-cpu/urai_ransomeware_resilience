from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.enums import (
    ArtifactStatus,
    DataProvenance,
    Decision,
    IncidentStage,
    Industry,
    OperationalImpactStatus,
    RuntimeState,
    Severity,
    SiteType,
)


NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class BackupReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latest_backup_age_hours: float | None = Field(default=None, ge=0.0)
    immutable_copy_available: bool | None = None
    last_restore_test_age_days: float | None = Field(default=None, ge=0.0)
    configuration_coverage_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    limitations: list[str] = Field(default_factory=list)


class ArtifactProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_name: NonBlankString
    version: NonBlankString
    checksum_sha256: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            pattern=r"^[0-9a-f]{64}$",
        ),
    ]
    status: ArtifactStatus


class OperationalDependencyImpact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: NonBlankString
    impact_status: OperationalImpactStatus
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    physical_safety_determination: Literal["not_determined"] = "not_determined"
    operational_state_claimed: Literal[False] = False


class RansomwareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: Literal["ransomware_resilience"]
    industry: Industry
    site_id: NonBlankString
    site_type: SiteType
    scenario_id: NonBlankString

    decision: Decision
    incident_stage: IncidentStage
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    resilience_score: float = Field(ge=0.0, le=100.0)

    affected_assets: list[str]
    suspected_assets: list[str]
    potentially_exposed_assets: list[str]
    protected_assets: list[str]
    unknown_assets: list[str]
    critical_services_at_risk: list[str]
    affected_zones: list[str]
    protected_boundaries: list[str]
    operational_dependency_impact: list[OperationalDependencyImpact]

    propagation_path: list[str]
    evidence_layers: list[str]
    triggered_rules: list[str]
    timeline: list[str]

    backup_readiness: BackupReadiness
    explanations: list[str]
    recommended_actions: list[str]

    human_approval_required: Literal[True]
    real_action_executed: Literal[False]

    artifact_provenance: list[ArtifactProvenance]
    data_provenance: DataProvenance
    warnings: list[str]

    request_id: NonBlankString
    trace_id: NonBlankString
    runtime_state: RuntimeState

    @model_validator(mode="after")
    def enforce_sector_site_type(self):
        permitted = {
            Industry.ENERGY: {SiteType.CONTROL_CENTRE, SiteType.SUBSTATION},
            Industry.PETROCHEMICAL: {
                SiteType.REFINERY,
                SiteType.PETROCHEMICAL_COMPLEX,
            },
        }
        if self.site_type not in permitted[self.industry]:
            raise ValueError("site_type is not permitted for industry")
        return self
