import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.orm import relationship

from app.models.base import Base

class AgentController(Base):
    __tablename__ = "agent_controllers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True)
    api_key = Column(String, nullable=False, unique=True)
    google_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    credit_balance = Column(Float, nullable=False, default=0)   # Using Int when price is per million tokens would be a bitch and life is too short
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    last_login = Column(DateTime, nullable=True)

    alert_prompts = relationship("AlertPrompt", back_populates="user")
    documents = relationship("UserDocument", back_populates="agent_controller")