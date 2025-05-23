from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector
import uuid

class LLMValidation(Base):
    __tablename__ = "llm_validations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_id = Column(String(36), ForeignKey('alert_prompts.id'), nullable=False)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    input_price = Column(Float, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    output_price = Column(Float, nullable=False)
    
    llm_id = Column(String(36), ForeignKey('llm_models.id'), nullable=False)
    date_time = Column(DateTime, nullable=False)