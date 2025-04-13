import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List

class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    
class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    

class AlertPrompt:
    id: uuid.UUID
    user_id: uuid.UUID  # reference to User
    prompt: str
    prompt_embedding: List[float]  # for vector similarity search
    status: AlertStatus
    created_at: datetime
    last_checked: datetime
    metadata: Dict  # flexible storage for different alert types
    response_format: Dict  # The format of the response from the alert
    parsed_intent: Dict  # The parsed intent of the alert
    example_response: Dict  # An example response from the alert
    min_datetime: datetime  # The minimum datetime of the alert
    max_datetime: datetime  # The maximum datetime of the alert
    http_method: HttpMethod  # The HTTP method of the alert
    http_url: str  # The URL of the alert
    tags: List[str]  # The tags of the alert
    # Example metadata:
    # {
    #   "type": "stock_price",
    #   "symbol": "TSLA",
    #   "threshold": 300
    # }
    # or
    # {
    #   "type": "news_topic",
    #   "keywords": ["AI", "regulation"],
    #   "sources": ["Reuters", "Bloomberg"]
    # }