from app.models.base import Base
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY

class LLMVerification(Base):
    __tablename__ = "llm_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_prompt_id = Column(UUID(as_uuid=True), ForeignKey('alert_prompts.id'), nullable=False)
    
    approval = Column(Boolean, nullable=False)
    chance_score = Column(Float, nullable=False)
    
    llm_model = Column(String, nullable=False)
    input_tokens_count = Column(Integer, nullable=False)
    input_tokens_price = Column(Float, nullable=False)
    output_tokens_count = Column(Integer, nullable=False)
    output_tokens_price = Column(Float, nullable=False)
    
    date_time = Column(DateTime, nullable=False)

