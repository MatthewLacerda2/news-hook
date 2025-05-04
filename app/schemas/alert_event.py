from app.models.base import Base
from datetime import datetime
from pydantic import Field
from typing import Dict, JsonPrimitive
from pydantic import ConfigDict

class NewsEvent(Base):

    id: str = Field(..., description="The ID of the alert event")
    alert_prompt_id: str = Field(..., description="The ID of the alert prompt")
    triggered_at: datetime = Field(..., description="The datetime the alert event was triggered")
    
    output: str = Field(..., description="The LLM output on the matter")
    tags: list[str] = Field(..., description="The tags for the alert")
    source_url: str = Field(..., description="The URL of the source that triggered the alert")
    structured_data: Dict[str, JsonPrimitive] = Field(..., description="The structured JSON response as requested by the alert requester")
    
    model_config = ConfigDict(from_attributes=True)