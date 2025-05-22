from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base

class APISource(Base):
    __tablename__ = "api_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    headers = Column(JSON, nullable=True)
    query_params = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    request_seconds_interval = Column(Integer, nullable=False)
    last_requested_at = Column(DateTime, nullable=True)
    num_requests = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    
    monitored_data = relationship("MonitoredData", back_populates="api_source")
