from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from app.models.alert_prompt import AlertStatus

class HttpMethod(str, Enum):
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"

class AlertPromptCreateRequestBase(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod = Field(..., description="HTTP method to alert at")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    http_headers: Optional[Dict] = Field(None, description="HTTP headers to send with the request")
    llm_model: str = Field("gemini-2.5-pro-preview-05-06", description="The LLM model to use for the alert")
    is_recurring: Optional[bool] = Field(None, description="Whether the alert is recurring")    #TODO: must NOT be optional
    
    # Optional fields
    payload_format: Optional[Dict] = Field(None, description="A JSON schema describing the expected payload (e.g., from .model_json_schema())")
    max_datetime: Optional[datetime] = Field(None, description="Monitoring window. Must be within the next 300 days")
    

    @field_validator('max_datetime')
    @classmethod
    def validate_max_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
            
        # Create timezone-aware now() if input is timezone-aware
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        max_allowed = now + timedelta(days=300)
        
        if v > max_allowed:
            raise ValueError("max_datetime cannot be more than 300 days in the future")
            
        return v
    
    #TODO: headers and payload validators

class AlertPromptCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    reason: str = Field(..., description="Reason for the approval or denial")
    created_at: datetime
    keywords: Optional[list[str]] = Field(None, description="Keywords that MUST be in the data that triggers the alert")

    model_config = ConfigDict(from_attributes=True)

class AlertPromptItem(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod
    http_url: HttpUrl
    http_headers: Optional[Dict] = Field(None, description="HTTP headers to send with the request")
    payload_format: Optional[Dict] = Field(None, description="A JSON schema describing the expected payload")
    is_recurring: bool = Field(..., description="Whether the alert is recurring")
    tags: List[str] = Field(default_factory=list, description="Tags for hinting")
    status: AlertStatus 
    created_at: datetime = Field(..., lt=datetime.now(), description="The date and time the alert was created")
    expires_at: datetime = Field(..., description="The date and time the alert will expire")
    llm_model: str = Field(..., description="The LLM model used to create the alert")

    model_config = ConfigDict(from_attributes=True)

class AlertPromptListResponse(BaseModel):
    alerts: list[AlertPromptItem]
    total_count: int

    model_config = ConfigDict(from_attributes=True)
    
class AlertCancelRequest(BaseModel):
    alert_id: str = Field(..., description="The ID of the alert to cancel")
    user_id: str = Field(..., description="The ID of the agent controller requesting to cancel the alert")