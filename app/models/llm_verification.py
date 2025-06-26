from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, JSON
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class LLMVerification(Base):
    __tablename__ = "llm_verifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_prompt_id = Column(String(36), ForeignKey('alert_prompts.id'), nullable=False)
    document_id = Column(String(36), ForeignKey('monitored_data.id'), nullable=False)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    keywords = Column(JSON, nullable=False)
    
    llm_model = Column(String, nullable=False)
    input_tokens_count = Column(Integer, nullable=False)
    input_tokens_price = Column(Float, nullable=False)
    output_tokens_count = Column(Integer, nullable=False)
    output_tokens_price = Column(Float, nullable=False)
    
    date_time = Column(DateTime, nullable=False)
    
    alert_prompt = relationship("AlertPrompt", back_populates="llm_verifications")
    monitored_data = relationship("MonitoredData")