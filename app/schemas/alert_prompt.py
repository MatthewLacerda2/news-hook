from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Union
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, field_validator
from app.models.alert_prompt import AlertStatus

JsonPrimitive = Union[str, int, float, bool, None]

class HttpMethod(str, Enum):
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"

class AlertPromptCreateRequestBase(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod = Field(..., description="HTTP method to alert at")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    http_headers: Optional[Dict[str, JsonPrimitive]] = Field(None, description="HTTP headers to send with the request")
    llm_model: str = Field("gemini-2.5-pro", description="The LLM model to use for the alert")
    
    # Optional fields
    parsed_intent: Optional[Dict[str, JsonPrimitive]] = Field(None, description="Parsed interpretation of the prompt. MUST BE FLAT JSON AND NOT NESTED")
    schema_format: Dict[str, JsonPrimitive] = Field(..., description="The schema of the response. MUST BE FLAT JSON AND NOT NESTED")
    max_datetime: Optional[datetime] = Field(None, description="Monitoring window. Must be within the next 300 days")
    

    @field_validator('max_datetime')
    @classmethod
    def validate_max_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
            
        now = datetime.now()
        max_allowed = now + timedelta(days=300)
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
    expire_datetime: Optional[datetime]
    tags: list[str] = Field(default=[], description="Tags for hinting")
    keywords: list[str] = Field(default=[], description="Mandatory keywords to be found in the monitored data")
    status: AlertStatus 
    created_at: datetime = Field(..., lt=datetime.now(), description="The date and time the alert was created")

    class Config:
        from_attributes = True

class AlertPromptListResponse(BaseModel):
    alerts: list[AlertPromptItem]
    total_count: int

    class Config:
        from_attributes = True

class AlertPromptPriceCheckRequest(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    # Optional fields
    parsed_intent: Optional[Dict[str, JsonPrimitive]] = Field(None, description="Parsed interpretation of the prompt")
    response_format: Optional[Dict[str, JsonPrimitive]] = Field(None, description="The schema of the response. MUST BE FLAT JSON AND NOT NESTED")

class AlertPromptPriceCheckSuccessResponse(BaseModel):
    price_in_credits: int
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What LLM understood from the prompt")
    
class AlertCancelRequest(BaseModel):
    alert_id: UUID = Field(..., description="The ID of the alert to cancel")
    user_id: UUID = Field(..., description="The ID of the agent controller requesting to cancel the alert")