import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class AgentController(Base):
    __tablename__ = "agent_controllers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    api_key = Column(String, nullable=False, unique=True)
    google_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    credits = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    alert_prompts = relationship("AlertPrompt", back_populates="user")