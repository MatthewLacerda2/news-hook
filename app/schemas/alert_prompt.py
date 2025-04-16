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
    PATCH = "PATCH"
    DELETE = "DELETE"

#TODO: check out for base, pro, reasoning
class AlertPromptCreateRequestBase(BaseModel):
    user_id: UUID = Field(..., description="ID of the agent controller requesting their alerts")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod = Field(..., description="HTTP method to alert at")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    
    # Optional fields
    parsed_intent: Optional[Dict[str, Any]] = Field(None, description="Parsed interpretation of the prompt")
    example_response: Optional[Dict[str, Any]] = Field(None, description="Example of expected response")
    max_datetime: Optional[datetime] = Field(None, description="Monitoring window. Must be within the next 300 days")

class AlertPromptCreateSuccessResponse(BaseModel):
    id: UUID = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What the LLM understood from the prompt")
    created_at: datetime
    keywords: Optional[list[str]] = Field(None, description="Keywords that will be expected to be in the data that triggers the alert")

    class Config:
        from_attributes = True

class AlertPromptListRequest(BaseModel):
    user_id: UUID = Field(..., description="ID of the agent controller requesting their alerts")
    tags: list[str] = Field(default=[], description="List of tags to filter alerts by")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    limit: int = Field(default=50, ge=1, le=100, description="Limit for pagination")
    
    # Optional filters
    prompt_contains: Optional[str] = Field(None, description="Substring to filter prompts by")
    http_method: Optional[HttpMethod] = Field(None, description="Filter by HTTP method")
    base_url: Optional[HttpUrl] = Field(None, description="Filter by base URL")
    max_datetime: Optional[datetime] = Field(None, description="Filter by max datetime")
    created_at: Optional[datetime] = Field(None, description="Filter by creation date")
    status: Optional[AlertStatus] = Field(None, description="Filter by alert status")

class AlertPromptItem(BaseModel):
    id: UUID
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod
    http_url: HttpUrl
    max_datetime: Optional[datetime]
    tags: list[str] = []
    keywords: list[str] = Field(default=[], description="List of keywords that will trigger the alert when found in monitored data")
    status: AlertStatus 
    created_at: datetime = Field(..., lt=datetime.now(), description="The date and time the alert was created")

    class Config:
        from_attributes = True

class AlertPromptListResponse(BaseModel):
    alerts: list[AlertPromptItem]
    total_count: int

    class Config:
        from_attributes = True

class AlertMode(str, Enum):
    base = "base"
    pro = "pro"
    reasoning = "reasoning"

class AlertPromptPriceCheckRequest(BaseModel):
    mode: AlertMode = Field(..., description="The mode of the alert. Used for pricing")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    # Optional fields
    parsed_intent: Optional[Dict[str, Any]] = Field(None, description="Parsed interpretation of the prompt")
    example_response: Optional[Dict[str, Any]] = Field(None, description="Example of expected response")

class AlertPromptPriceCheckSuccessResponse(BaseModel):
    price_in_credits: int
    mode: AlertMode = Field(..., description="The mode of the alert. Used for pricing")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What LLM understood from the prompt")
    
class AlertCancelRequest(BaseModel):
    alert_id: UUID = Field(..., description="The ID of the alert to cancel")
    user_id: UUID = Field(..., description="The ID of the agent controller requesting to cancel the alert")

