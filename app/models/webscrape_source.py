from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class WebscrapeSource(Base):
    __tablename__ = "webscrape_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    scrape_seconds_interval = Column(Integer, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)
    headers = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    num_scrapes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with MonitoredData
    monitored_data = relationship("MonitoredData", back_populates="webscrape_source")
