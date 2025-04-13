from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from app.models.alert_prompt import AlertStatus

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

#TODO: check out for base, pro, reasoning
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

class AlertPromptListRequest(BaseModel):
    user_id: UUID = Field(..., description="ID of the agent controller requesting their alerts")
    tags: list[str] = Field(default=[], description="List of tags to filter alerts by")
    offset: int = Field(default=0, description="Offset for pagination")
    limit: int = Field(default=50, description="Limit for pagination")
    
    # Optional filters
    prompt_contains: Optional[str] = Field(None, description="Substring to filter prompts by")
    http_method: Optional[HttpMethod] = Field(None, description="Filter by HTTP method")
    base_url: Optional[HttpUrl] = Field(None, description="Filter by base URL")
    max_datetime: Optional[datetime] = Field(None, description="Filter by max datetime")
    created_at: Optional[datetime] = Field(None, description="Filter by creation date")
    status: Optional[AlertStatus] = Field(None, description="Filter by alert status")

class AlertPromptItem(BaseModel):
    id: UUID
    prompt: str
    http_method: HttpMethod
    http_url: HttpUrl
    max_datetime: Optional[datetime]
    tags: list[str] = []
    status: AlertStatus
    created_at: datetime

    class Config:
        from_attributes = True

class AlertPromptListResponse(BaseModel):
    alerts: list[AlertPromptItem]
    total_count: int

    class Config:
        from_attributes = True
