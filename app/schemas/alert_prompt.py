from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Union, List
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from app.models.alert_prompt import AlertStatus

JsonPrimitive = Union[str, int, float, bool, datetime]
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
    payload_format: Optional[Dict[str, JsonPrimitive]] = Field(None, description="The schema of the response. MUST BE FLAT JSON AND NOT NESTED")
    max_datetime: Optional[datetime] = Field(None, description="Monitoring window. Must be within the next 300 days")
    

    @field_validator('max_datetime')
    @classmethod
    def validate_max_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
            
        now = datetime.now()
        max_allowed = now + timedelta(days=300)
        if v > max_allowed:
            raise ValueError("max_datetime cannot be more than 300 days in the future")
            
        return v

    @field_validator('parsed_intent')
    @classmethod
    def check_flat_json_parsed_intent(cls, v):
        if v is not None:
            for key, value in v.items():
                if isinstance(value, (dict, list)):
                    raise ValueError("parsed_intent must be flat (no nested objects or arrays)")
        return v

    @field_validator('payload_format')
    @classmethod
    def check_flat_json_payload_format(cls, v):
        if v is not None:
            for key, value in v.items():
                if isinstance(value, (dict, list)):
                    raise ValueError("payload_format must be flat (no nested objects or arrays)")
        return v

class AlertPromptCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What the LLM understood from the prompt")
    created_at: datetime
    keywords: Optional[list[str]] = Field(None, description="Keywords that MUST be in the data that triggers the alert")

    model_config = ConfigDict(from_attributes=True)

class AlertPromptItem(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    http_method: HttpMethod
    http_url: HttpUrl
    http_headers: Optional[Dict[str, JsonPrimitive]] = Field(None, description="HTTP headers to send with the request")
    expires_at: datetime = Field(..., description="The date and time the alert will expire")
    payload_format: Optional[Dict[str, JsonPrimitive]] = Field(None, description="The schema of the response. MUST BE FLAT JSON AND NOT NESTED")
    tags: List[str] = Field(default_factory=list, description="Tags for hinting")
    status: AlertStatus 
    created_at: datetime = Field(..., lt=datetime.now(), description="The date and time the alert was created")
    llm_model: str = Field(..., description="The LLM model used to create the alert")

    model_config = ConfigDict(from_attributes=True)

class AlertPromptListResponse(BaseModel):
    alerts: list[AlertPromptItem]
    total_count: int

    model_config = ConfigDict(from_attributes=True)

class AlertPromptPriceCheckRequest(BaseModel):
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    # Optional fields
    parsed_intent: Optional[Dict[str, JsonPrimitive]] = Field(None, description="Parsed interpretation of the prompt")
    payload_format: Optional[Dict[str, JsonPrimitive]] = Field(None, description="The schema of the response. MUST BE FLAT JSON AND NOT NESTED")

class AlertPromptPriceCheckSuccessResponse(BaseModel):
    price_in_credits: int
    prompt: str = Field(..., description="The natural language prompt describing what to monitor")
    output_intent: str = Field(..., description="What LLM understood from the prompt")
    
class AlertCancelRequest(BaseModel):
    alert_id: str = Field(..., description="The ID of the alert to cancel")
    user_id: str = Field(..., description="The ID of the agent controller requesting to cancel the alert")