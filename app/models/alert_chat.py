import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Index
import uuid
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.utils.env import NUM_EMBEDDING_DIMENSIONS
from app.models.base import Base

class AlertChatStatus(Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    CANCELLED = "CANCELLED"
    WARNED = "WARNED"
    EXPIRED = "EXPIRED"


class AlertChat(Base):
    __tablename__ = "alert_chats"
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_prompt_embedding_cosine', 'prompt_embedding', postgresql_using='ivfflat', postgresql_ops={'prompt_embedding': 'vector_cosine_ops'}),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(String(36), nullable=False)
    prompt = Column(String, nullable=False)
    prompt_embedding = Column(Vector(NUM_EMBEDDING_DIMENSIONS), nullable=True)
    
    keywords = Column(JSON, nullable=False)
    status = Column(SQLEnum(AlertChatStatus), nullable=False, default=AlertChatStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    expires_at = Column(DateTime, nullable=False)

    alert_events = relationship("AlertEvent", back_populates="alert_chat")
    llm_validations = relationship("LLMValidation", back_populates="alert_chat")
    llm_verifications = relationship("LLMVerification", back_populates="alert_chat")