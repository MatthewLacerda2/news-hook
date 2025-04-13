import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base

class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    WARNED = "warned"
    EXPIRED = "expired"
    
class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    

class AlertPrompt(Base):
    __tablename__ = "alert_prompts"
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('agent_controllers.id'), nullable=False)
    prompt = Column(String, nullable=False)
    http_method = Column(SQLEnum(HttpMethod), nullable=True)
    http_url = Column(String, nullable=True)
    
    parsed_intent = Column(JSON, nullable=True)
    example_response = Column(JSON, nullable=True)
    max_datetime = Column(DateTime, nullable=True)
    
    tags = Column(ARRAY(String), nullable=True)
    prompt_embedding = Column(ARRAY(float), nullable=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("AgentController", back_populates="alert_prompts")
    alert_events = relationship("AlertEvent", back_populates="alert_prompt")