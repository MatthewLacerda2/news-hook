from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector

class LLMValidation(Base):
    __tablename__ = "llm_validations"
    
    id = Column(Integer, primary_key=True)
    prompt = Column(String, nullable=False)
    prompt_embedding = Column(Vector(384), nullable=False)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey('alert_prompts.id'), nullable=False)
    
    parsed_intent = Column(String, nullable=False)
    parsed_intent_embedding = Column(Vector(384), nullable=False)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    input_price = Column(Float, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    output_price = Column(Float, nullable=False)
    
    llm_id = Column(UUID(as_uuid=True), ForeignKey('llm_models.id'), nullable=False)
    date_time = Column(DateTime, nullable=False)