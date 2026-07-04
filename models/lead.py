from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from datetime import datetime
from database.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String)
    job_title = Column(String)
    company_name = Column(String)

    company_website = Column(String)
    linkedin_url = Column(String)

    email = Column(String)
    email_status = Column(String)          # legacy string status kept for compat
    email_verified = Column(Boolean, default=False)   # NEW: Boolean flag
    email_source = Column(String)          # NEW: INFERRED / FOUND / VERIFIED

    phone = Column(String)
    phone_status = Column(String)          # legacy string status kept for compat
    phone_verified = Column(Boolean, default=False)   # NEW: Boolean flag
    phone_source = Column(String)          # NEW: FOUND / VERIFIED
    line_type = Column(String)             # NEW: mobile / landline / voip

    industry = Column(String)

    employee_count = Column(Integer)       # NEW
    founding_year = Column(Integer)        # NEW

    source_url = Column(String)            # NEW
    scraped_date = Column(DateTime)        # NEW

    confidence_score = Column(Integer)
    confidence_level = Column(String)

    role_verified = Column(Boolean, default=False)

    source = Column(String)

    status = Column(String, default="New")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # NEW
