from pydantic import BaseModel

class RansomwareRequest(BaseModel):
    industry:str
    site_id:str
    site_type:str
    scenario_id:str
    schema_version:str