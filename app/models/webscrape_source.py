from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base

class WebscrapeSource(Base):
    __tablename__ = "webscrape_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    scrape_seconds_interval = Column(Integer, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)
    headers = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    num_scrapes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with MonitoredData
    monitored_data = relationship("MonitoredData", back_populates="webscrape_source")
