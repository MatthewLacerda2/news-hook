from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Dict, Any
from app.models.alert_prompt import HttpMethod

class AlertEventItem(BaseModel):
    #ALERT_EVENT MODEL FIELDS
    id: str = Field(..., description="The ID of the alert event")
    alert_prompt_id: str = Field(..., description="The ID of the alert prompt")
    triggered_at: datetime = Field(..., description="The datetime the alert event was sent")
    structured_data: Dict[str, Any] = Field(..., description="The json schema requested for the alert")
    status_code: int = Field(..., description="The status code of the response")
    
    #ALERT_PROMPT MODEL FIELDS
    prompt: str = Field(..., description="The alert prompt that this event answered to")    
    http_method: HttpMethod = Field(..., description="The HTTP method used at the URL")
    http_url: HttpUrl = Field(..., description="The HTTP URL that the alert event was sent to")
    is_recurring: bool = Field(..., description="Whether the alert is recurring or not")
    
    model_config = ConfigDict(from_attributes=True)
    
class AlertEventListResponse(BaseModel):
    events: list[AlertEventItem]
    total_count: int
    
    model_config = ConfigDict(from_attributes=True)