from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.enums import Industry, SiteType


NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
RESERVED_TRUTH_KEYS = {
    "ground_truth",
    "ground_truth_label",
    "synthetic_truth",
    "truth_label",
}


def _find_reserved_truth_key(value: Any, path: str = "observable_input") -> str | None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).strip().lower()
            current_path = f"{path}.{key}"
            if normalized_key in RESERVED_TRUTH_KEYS:
                return current_path
            nested_match = _find_reserved_truth_key(nested_value, current_path)
            if nested_match:
                return nested_match
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            nested_match = _find_reserved_truth_key(
                nested_value,
                f"{path}[{index}]",
            )
            if nested_match:
                return nested_match
    return None


class RansomwareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    use_case: Literal["ransomware_resilience"]
    industry: Industry
    site_id: NonBlankString
    site_type: SiteType
    scenario_id: NonBlankString
    observable_input: dict[str, Any]

    @field_validator("observable_input")
    @classmethod
    def reject_ground_truth(cls, value: dict) -> dict:
        truth_path = _find_reserved_truth_key(value)
        if truth_path:
            raise ValueError(
                f"reserved synthetic-truth field is not allowed: {truth_path}"
            )
        return value
