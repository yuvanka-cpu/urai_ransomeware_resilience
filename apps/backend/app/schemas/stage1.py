from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import Industry, SiteType


class AcceptanceMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(pattern=r"^(EN|PC)-RW-0[1-5]-M[0-9]{2}$")
    metric: str = Field(min_length=1)
    operator: Literal["gte", "lte", "before", "equals", "reported_separately"]
    value: float | str | bool
    unit: Literal[
        "ratio",
        "percent",
        "incident_stage",
        "boolean",
        "reporting_requirement",
    ]
    sector_report_required: Literal[True] = True


class UseCaseContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str = Field(pattern=r"^(EN|PC)-RW-0[1-5]$")
    industry: Industry
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    scenario_family: str = Field(min_length=1)
    site_types: list[SiteType] = Field(min_length=1)
    principal_assets: list[str] = Field(min_length=1)
    observable_evidence: list[str] = Field(min_length=1)
    dashboard_outputs: list[str] = Field(min_length=1)
    recommendation_template_id: str = Field(pattern=r"^(EN|PC)-REC-0[1-5]$")
    protected_boundary_context: list[str] = Field(default_factory=list)
    safety_statement: str = Field(min_length=1)
    acceptance_metric_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_sector_prefix(self):
        expected_prefix = "EN" if self.industry == Industry.ENERGY else "PC"
        if not self.use_case_id.startswith(expected_prefix):
            raise ValueError("use-case ID does not match industry")
        if not self.recommendation_template_id.startswith(expected_prefix):
            raise ValueError("recommendation template does not match industry")
        for metric_id in self.acceptance_metric_ids:
            if not metric_id.startswith(f"{self.use_case_id}-M"):
                raise ValueError("acceptance metric ID does not match use case")
        return self


class UseCaseCatalogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    industry: Industry
    use_cases: list[UseCaseContract] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validate_catalogue(self):
        ids = [use_case.use_case_id for use_case in self.use_cases]
        if len(ids) != len(set(ids)):
            raise ValueError("use-case IDs must be unique")
        if any(use_case.industry != self.industry for use_case in self.use_cases):
            raise ValueError("catalogue contains an incorrect industry")
        return self


class RecommendationTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(pattern=r"^(EN|PC)-REC-0[1-5]$")
    use_case_id: str = Field(pattern=r"^(EN|PC)-RW-0[1-5]$")
    industry: Industry
    review_prompts: list[str] = Field(min_length=1)
    warnings: list[str] = Field(min_length=1)
    safety_statements: list[str] = Field(min_length=1)
    human_approval_required: Literal[True]
    real_action_executed: Literal[False]

    @model_validator(mode="after")
    def validate_sector_and_use_case(self):
        expected_prefix = "EN" if self.industry == Industry.ENERGY else "PC"
        if not self.template_id.startswith(expected_prefix):
            raise ValueError("recommendation template does not match industry")
        expected_use_case = self.template_id.replace("-REC-", "-RW-")
        if self.use_case_id != expected_use_case:
            raise ValueError("recommendation template does not match use case")
        return self


class AssetStateDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal[
        "confirmed_affected",
        "suspected",
        "potentially_exposed",
        "protected",
        "unknown",
    ]
    meaning: str = Field(min_length=1)
    minimum_evidence: str = Field(min_length=1)
    must_not_claim: str = Field(min_length=1)


class AcceptanceGateFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    reporting_rule: Literal["separate_energy_and_petrochemical"]
    use_cases: dict[str, list[AcceptanceMetric]]

    @model_validator(mode="after")
    def validate_gate_mapping(self):
        if len(self.use_cases) != 10:
            raise ValueError("acceptance gates must cover exactly ten use cases")
        for use_case_id, metrics in self.use_cases.items():
            expected_ids = {metric.metric_id for metric in metrics}
            if len(expected_ids) != len(metrics):
                raise ValueError(f"duplicate metric ID for {use_case_id}")
            if any(not metric_id.startswith(f"{use_case_id}-M") for metric_id in expected_ids):
                raise ValueError(f"metric ID does not match {use_case_id}")
        return self
