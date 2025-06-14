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
    credit_balance = Column(Float, nullable=False, default=10.00)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    last_login = Column(DateTime, nullable=True)

    alert_prompts = relationship("AlertPrompt", back_populates="user")
    monitored_data = relationship("MonitoredData", back_populates="agent_controller")