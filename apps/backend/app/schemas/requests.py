from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RansomwareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    use_case: Literal["ransomware_resilience"]
    industry: Literal["Energy", "Petrochemical"]
    site_id: str = Field(min_length=1)
    site_type: Literal[
        "control_centre",
        "substation",
        "refinery",
        "petrochemical_complex",
    ]
    scenario_id: str = Field(min_length=1)
    observable_input: dict

    @field_validator("observable_input")
    @classmethod
    def reject_ground_truth(cls, value: dict) -> dict:
        if "ground_truth" in value:
            raise ValueError(
                "ground_truth is not allowed in observable_input"
            )
        return value