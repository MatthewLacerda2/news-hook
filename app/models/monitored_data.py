import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base

class DataSource(Enum):
    WEBHOOK = "webhook"
    WEBSCRAPE = "webscrape"
    API = "api"

class MonitoredData(Base):
    __tablename__ = "monitored_data"
    __table_args__ = (
        Index('idx_scraped_datetime', 'scraped_datetime'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(SQLEnum(DataSource), nullable=False)
    source_url = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    content_embedding = Column(ARRAY(float), nullable=True)
    scraped_datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys for different source types
    webhook_source_id = Column(UUID(as_uuid=True), ForeignKey('webhook_sources.id'), nullable=True)
    api_source_id = Column(UUID(as_uuid=True), ForeignKey('api_sources.id'), nullable=True)
    webscrape_source_id = Column(UUID(as_uuid=True), ForeignKey('webscrape_sources.id'), nullable=True)
    
    # Relationships
    webhook_source = relationship("WebhookSource", back_populates="monitored_data")
    api_source = relationship("APISource", back_populates="monitored_data")
    webscrape_source = relationship("WebscrapeSource", back_populates="monitored_data")
