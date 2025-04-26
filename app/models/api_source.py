from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class APISource(Base):
    __tablename__ = "api_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    method = Column(String, default="GET")
    headers = Column(JSON, nullable=True)
    query_params = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    request_seconds_interval = Column(Integer, nullable=False)
    last_requested_at = Column(DateTime, nullable=True)
    num_requests = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)
    
    # Relationship with MonitoredData
    monitored_data = relationship("monitored_data", back_populates="api_source")
