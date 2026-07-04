from sqlalchemy import Column, Integer, String, Float
from database.db import Base


class Company(Base):

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, unique=True, index=True, nullable=False)

    founder = Column(String, nullable=True)

    founded = Column(String, nullable=True)

    source = Column(String, nullable=True)

    website = Column(String, nullable=True)

    confidence_score = Column(Float, default=0.0, nullable=False)

    # NEW fields required by spec
    industry = Column(String, nullable=True)
    employee_count = Column(Integer, nullable=True)
    country = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)