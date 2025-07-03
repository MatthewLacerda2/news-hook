from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from app.models.alert_prompt import AlertStatus, HttpMethod
from app.utils.env import MAX_DATETIME, FLAGSHIP_MODEL

class AlertPromptCreateRequestBase(BaseModel):
    prompt: str = Field(..., description="The description of what to monitor. Try to be specific, clear and succinct.")
    http_url: HttpUrl = Field(..., description="The URL to alert at")
    http_headers: Optional[Dict] = Field(None, description="HTTP headers to send with the request")
    is_recurring: Optional[bool] = Field(None, description="Should we send the alert every time the condition is met?")
    
    # Optional fields
    http_method: Optional[HttpMethod] = Field(default=HttpMethod.POST, description="HTTP method to alert at")
    llm_model: Optional[str] = Field(default=FLAGSHIP_MODEL, description="The LLM model to use for the alert")
    max_datetime: Optional[datetime] = Field(None, description=f"Monitoring window. Must be within the next {MAX_DATETIME} days")
    

    @field_validator('max_datetime')
    @classmethod
    def validate_max_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v

        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        max_allowed = now + timedelta(days=MAX_DATETIME)
        
        if v > max_allowed:
            raise ValueError(f"max_datetime cannot be more than {MAX_DATETIME} days in the future")
            
        return v
    
    @field_validator('http_headers')
    @classmethod
    def validate_headers(cls, v: Optional[Dict]) -> Optional[Dict]:
        if v is None:
            return v

        for header_name, header_value in v.items():
            if not isinstance(header_name, str):
                raise ValueError(f"Header name must be a string, got {type(header_name)}")
                
            if isinstance(header_value, list):
                if not all(isinstance(x, str) for x in header_value):
                    raise ValueError(f"All header values in list must be strings for header: {header_name}")
            elif not isinstance(header_value, str):
                raise ValueError(f"Header value must be a string or list of strings, got {type(header_value)}")
                
        return v

class AlertPromptCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    prompt: str = Field(..., description="The description of what to monitor")
    reason: str = Field(..., description="Reason for the approval or denial")
    created_at: datetime
    keywords: Optional[list[str]] = Field(None, description="keywords required to be in the document that triggers the alert")

    model_config = ConfigDict(from_attributes=True)

class AlertPromptItem(BaseModel):
    id: str = Field(..., description="The ID of the alert")
    #Using more than 1024 characters is moronic
    prompt: str = Field(..., lte = 1024, description="The description of what to monitor. Try to be specific, clear and succinct.")
    http_method: HttpMethod
    http_url: HttpUrl
    http_headers: Optional[Dict] = Field(None, description="HTTP headers to send with the request")
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

class AlertPatchRequest(BaseModel):
    http_url: HttpUrl = Field(None, description="The URL to alert at")
    http_headers: Optional[Dict] = Field(None, description="HTTP headers to send with the request")
    is_recurring: Optional[bool] = Field(None, description="Should we send the alert every time the condition is met?")
    http_method: Optional[HttpMethod] = Field(None, description="HTTP method to alert at")
    llm_model: Optional[str] = Field(None, description="The LLM model to use for the alert")
    max_datetime: Optional[datetime] = Field(None, description=f"Monitoring window. Must be within the next {MAX_DATETIME} days")