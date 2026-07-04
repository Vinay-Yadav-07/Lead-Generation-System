from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeadCreate(BaseModel):
    full_name: str
    job_title: str
    company_name: str


class LeadStatusUpdate(BaseModel):
    status: str


class LeadResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    linkedin_url: Optional[str] = None

    email: Optional[str] = None
    email_status: Optional[str] = None
    email_verified: Optional[bool] = False
    email_source: Optional[str] = None

    phone: Optional[str] = None
    phone_status: Optional[str] = None
    phone_verified: Optional[bool] = False
    phone_source: Optional[str] = None
    line_type: Optional[str] = None

    industry: Optional[str] = None
    employee_count: Optional[int] = None
    founding_year: Optional[int] = None

    source_url: Optional[str] = None
    scraped_date: Optional[datetime] = None

    confidence_score: Optional[int] = None
    confidence_level: Optional[str] = None
    role_verified: Optional[bool] = False

    source: Optional[str] = None
    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
