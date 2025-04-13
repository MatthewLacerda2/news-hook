import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        Index('idx_triggered_at', 'triggered_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_prompt_id = Column(UUID(as_uuid=True), ForeignKey('alert_prompts.id'), nullable=False)
    scraped_data_id = Column(UUID(as_uuid=True), ForeignKey('monitored_data.id'), nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    response = Column(JSON, nullable=True)

    # Relationships
    alert_prompt = relationship("AlertPrompt", back_populates="alert_events")
    monitored_data = relationship("MonitoredData")
