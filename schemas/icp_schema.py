from pydantic import BaseModel
from typing import Optional


class ICPConfig(BaseModel):
    job_titles: list[str]
    industry: str
    country: str
    company_size: Optional[str] = None      # e.g. "10-500" — spec field
    employee_min: int = 0
    employee_max: int = 10000
    founding_year: Optional[int] = None     # NEW: spec required field
