import uuid
from datetime import datetime
from typing import Dict, List
from enum import Enum


class DataSource(Enum):
    WEBHOOK = "webhook"
    WEBSCRAPE = "webscrape"
    API = "api"
    

class MonitoredData:
    id: uuid.UUID
    source: DataSource
    source_url: str
    content: Dict
    content_embedding: List[float]  # for matching with alerts
    scraped_datetime: datetime
