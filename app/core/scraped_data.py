import uuid
from datetime import datetime
from typing import Dict, List

class ScrapedData:
    id: uuid.UUID
    source: str  # e.g., 'webscraping', 'webhook', 'news_api'
    source_url: str
    content: Dict  # raw data
    content_embedding: List[float]  # for matching with alerts
    scraped_at: datetime
    processed: bool  # track if we've checked this against alerts
