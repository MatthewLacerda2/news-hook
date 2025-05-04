import datetime
from pydantic import ConfigDict
from app.models.base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
import uuid
from sqlalchemy.orm import relationship

class UserDocumentChunk(Base):
    __tablename__ = "user_document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_document_id = Column(String(36), nullable=False)
    agent_controller_id = Column(String(36), ForeignKey('agent_controllers.id'), nullable=False)
    uploaded_datetime = Column(DateTime, nullable=False, default=datetime.now())
    chunk_index = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    content_embedding = Column(Vector(384), nullable=True)
    
    model_config = ConfigDict(from_attributes=True)

    agent_controller = relationship("AgentController", back_populates="document_chunks")
    user_document = relationship("UserDocument", back_populates="chunks")