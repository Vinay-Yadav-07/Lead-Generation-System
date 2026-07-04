from sqlalchemy import Column, Integer, String
from database.db import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(Integer)

    source = Column(String)

    field_name = Column(String)

    field_value = Column(String)