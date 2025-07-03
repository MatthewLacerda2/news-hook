import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, ForeignKey, Index, Float, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base

class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        Index('idx_triggered_at', 'triggered_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_prompt_id = Column(String(36), ForeignKey('alert_prompts.id'), nullable=True)
    alert_chat_id = Column(String(36), ForeignKey('alert_chats.id'), nullable=True)
    scraped_data_id = Column(String(36), ForeignKey('monitored_data.id'), nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.now())
    input_tokens = Column(Integer, nullable=False)
    input_price = Column(Float, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    output_price = Column(Float, nullable=False)
    structured_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=False)

    alert_prompt = relationship("AlertPrompt", back_populates="alert_events")
    alert_chat = relationship("AlertChat", back_populates="alert_events")
    monitored_data = relationship("MonitoredData")
