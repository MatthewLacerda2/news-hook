import datetime
from pydantic import ConfigDict
from app.models.base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, DateTime, ForeignKey
import uuid
from sqlalchemy.orm import relationship

class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_controller_id = Column(String(36), ForeignKey('agent_controllers.id'), nullable=False)
    name = Column(String(36), nullable=False)
    content = Column(String, nullable=False)
    content_embedding = Column(Vector(768), nullable=True)
    uploaded_datetime = Column(DateTime, nullable=False)
    
    model_config = ConfigDict(from_attributes=True)

    agent_controller = relationship("AgentController", back_populates="documents")