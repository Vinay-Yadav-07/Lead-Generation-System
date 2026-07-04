from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database.db import Base


class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, index=True)
    channel = Column(String, default="email")
    subject = Column(String)
    body = Column(String)
    status = Column(String, default="Drafted")
    provider_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
