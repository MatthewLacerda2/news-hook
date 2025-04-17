from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, field_validator
from app.models.alert_prompt import AlertStatus

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

#TODO: check out for base, pro, reasoning
class AlertPromptCreateRequestBase(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod = Field(..., description="HTTP method to alert at")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    
    # Optional fields
    parsed_intent: Optional[Dict[str, Any]] = Field(None, description="Parsed interpretation of the prompt")
    example_response: Optional[Dict[str, Any]] = Field(None, description="Example of expected response")
    max_datetime: Optional[datetime] = Field(None, description="Monitoring window. Must be within the next 300 days")

    @field_validator('max_datetime')
    @classmethod
    def validate_max_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
            
        now = datetime.utcnow()
        max_allowed = now + timedelta(days=365)
        if v > max_allowed:
            raise ValueError("max_datetime cannot be more than 1 year in the future")
            
        return v

class AlertPromptCreateSuccessResponse(BaseModel):
    id: UUID = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What the LLM understood from the prompt")
    created_at: datetime
    keywords: Optional[list[str]] = Field(None, description="Keywords that will be expected to be in the data that triggers the alert")

    class Config:
        from_attributes = True

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

