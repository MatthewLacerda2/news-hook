from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class AlertPromptCreateBase(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod = Field(..., description="HTTP method to alert at")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    
    # Optional fields
    parsed_intent: Optional[Dict[str, Any]] = Field(None, description="Parsed interpretation of the prompt")
    example_response: Optional[Dict[str, Any]] = Field(None, description="Example of expected response")
    max_datetime: Optional[datetime] = Field(None, description="End of monitoring window")

class AlertPromptCreateResponse(BaseModel):
    id: UUID
    prompt: str
    understood_intent: str
    created_at: datetime
    tags: Optional[list[str]] = None

    class Config:
        from_attributes = True

class AlertPromptCancelBase(BaseModel):
    id: UUID
