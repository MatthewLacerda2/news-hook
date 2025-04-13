from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class WebhookSource(Base):
    __tablename__ = "webhook_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    endpoint_path = Column(String, nullable=False, unique=True)
    secret_key = Column(String, nullable=False)
    expected_format = Column(JSON, nullable=True)
    validation_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    num_events = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with MonitoredData
    monitored_data = relationship("MonitoredData", back_populates="webhook_source")
