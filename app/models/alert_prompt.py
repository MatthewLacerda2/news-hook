import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base

class AlertStatus(Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    CANCELLED = "CANCELLED"
    WARNED = "WARNED"
    EXPIRED = "EXPIRED"
    
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
        Index('idx_prompt_embedding_cosine', 'prompt_embedding', postgresql_using='ivfflat', postgresql_ops={'prompt_embedding': 'vector_cosine_ops'}),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('agent_controllers.id'), nullable=False)
    prompt = Column(String, nullable=False)
    http_method = Column(SQLEnum(HttpMethod), nullable=False)
    http_url = Column(String, nullable=False)
    
    parsed_intent = Column(JSON, nullable=False)
    example_response = Column(JSON, nullable=False)
    max_datetime = Column(DateTime, nullable=False)
    
    tags = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=False)
    prompt_embedding = Column(Vector(384), nullable=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("AgentController", back_populates="alert_prompts")
    alert_events = relationship("AlertEvent", back_populates="alert_prompt")