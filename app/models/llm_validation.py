from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy import ForeignKey
import uuid
from sqlalchemy.orm import relationship

class LLMValidation(Base):
    __tablename__ = "llm_validations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_id = Column(String(36), ForeignKey('alert_prompts.id'), nullable=True)
    #TODO: what about alert_chats?
    prompt = Column(String(255), nullable=False)
    reason = Column(String(128), nullable=False)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    input_price = Column(Float, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    output_price = Column(Float, nullable=False)
    
    llm_model = Column(String, nullable=False)
    date_time = Column(DateTime, nullable=False)
    
    alert_prompt = relationship("AlertPrompt", back_populates="llm_validations")