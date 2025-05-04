from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector
import uuid

#TODO: we can remove the prompt, prompt_embedding, parsed_intent, parsed_intent_embedding columns
class LLMValidation(Base):
    __tablename__ = "llm_validations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = Column(String, nullable=False)
    prompt_embedding = Column(Vector(768), nullable=True)
    prompt_id = Column(String(36), ForeignKey('alert_prompts.id'), nullable=False)
    
    parsed_intent = Column(String, nullable=False)
    parsed_intent_embedding = Column(Vector(768), nullable=True)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    input_price = Column(Float, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    output_price = Column(Float, nullable=False)
    
    llm_id = Column(String(36), ForeignKey('llm_models.id'), nullable=False)
    date_time = Column(DateTime, nullable=False)