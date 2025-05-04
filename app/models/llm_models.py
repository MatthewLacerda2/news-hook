from sqlalchemy import Column, String, Float, Boolean
from app.models.base import Base
import uuid

class LLMModel(Base):
    __tablename__ = "llm_models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False, unique=True)
    input_token_price = Column(Float, nullable=False)
    output_token_price = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)