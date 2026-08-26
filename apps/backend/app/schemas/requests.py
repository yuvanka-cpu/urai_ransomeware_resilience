from pydantic import BaseModel


class RansomwareRequest(BaseModel):
    schema_version: str
    use_case: str
    industry: str
    site_id: str
    site_type: str
    scenario_id: str
    observable_input: dict