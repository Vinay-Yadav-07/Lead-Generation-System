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
    template_variant = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
