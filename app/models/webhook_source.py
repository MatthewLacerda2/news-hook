from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base

class WebhookSource(Base):
    __tablename__ = "webhook_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    endpoint_path = Column(String, nullable=False, unique=True)
    secret_key = Column(String, nullable=False)
    schema_format = Column(JSON, nullable=True)
    validation_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    num_events = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with MonitoredData
    monitored_data = relationship("MonitoredData", back_populates="webhook_source")
