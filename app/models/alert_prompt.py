import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List

class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    WARNED = "warned"
    EXPIRED = "expired"
    
class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    

class AlertPrompt:
    id: uuid.UUID
    user_id: uuid.UUID
    prompt: str
    prompt_embedding: List[float]  # for vector similarity search
    status: AlertStatus
    created_at: datetime
    parsed_intent: Dict
    example_response: Dict
    min_datetime: datetime
    max_datetime: datetime
    http_method: HttpMethod
    http_url: str
    tags: List[str]