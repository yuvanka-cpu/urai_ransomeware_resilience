from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SupplyChainUseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: Literal["SC-FW-SW-01"]
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    attack_scope: list[str] = Field(min_length=1)
    observable_evidence: list[str] = Field(min_length=1)
    affected_assets: list[str] = Field(min_length=1)
    dashboard_outputs: list[str] = Field(min_length=1)
    safety_boundaries: list[str] = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    human_approval_required: Literal[True]
    real_action_executed: Literal[False]


class SupplyChainUseCaseCatalogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    domain: Literal["supply_chain"]
    use_cases: list[SupplyChainUseCase] = Field(min_length=1)
