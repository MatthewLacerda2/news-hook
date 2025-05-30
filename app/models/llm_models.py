from sqlalchemy import Column, String, Float, Boolean
from app.models.base import Base

class LLMModel(Base):
    __tablename__ = "llm_models"
    
    model_name = Column(String, primary_key=True)
    input_token_price = Column(Float, nullable=False)
    output_token_price = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)