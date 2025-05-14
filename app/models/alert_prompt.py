import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index, Boolean, Integer
import uuid
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
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    

class AlertPrompt(Base):
    __tablename__ = "alert_prompts"
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_prompt_embedding_cosine', 'prompt_embedding', postgresql_using='ivfflat', postgresql_ops={'prompt_embedding': 'vector_cosine_ops'}),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_controller_id = Column(String(36), ForeignKey('agent_controllers.id'), nullable=False)
    prompt = Column(String, nullable=False)
    http_method = Column(SQLEnum(HttpMethod), nullable=False)
    http_url = Column(String, nullable=False)
    http_headers = Column(JSON, nullable=True)    
    payload_format = Column(JSON, nullable=True)
    
    is_recurring = Column(Boolean, nullable=False, default=False)
    
    keywords = Column(JSON, nullable=False)
    prompt_embedding = Column(Vector(768), nullable=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    expires_at = Column(DateTime, nullable=False)
    llm_model = Column(String, nullable=False)

    # Relationships
    user = relationship("AgentController", back_populates="alert_prompts")
    alert_events = relationship("AlertEvent", back_populates="alert_prompt")
    llm_validations = relationship("LLMValidation", back_populates="alert_prompt")