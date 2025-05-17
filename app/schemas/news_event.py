from app.models.base import Base
from datetime import datetime
from pydantic import Field
from typing import Dict, Any
from pydantic import ConfigDict

class NewsEvent(Base):

    id: str = Field(..., description="The ID of the alert event")
    document_id: str = Field(..., description="The ID of the document that triggered the alert")
    alert_prompt_id: str = Field(..., description="The ID of the alert prompt")
    triggered_at: datetime = Field(..., description="The datetime the alert event was triggered")
    
    output: str = Field(..., description="The LLM output on the matter")
    tags: list[str] = Field(..., description="The tags for the alert")
    source_url: str = Field(..., description="The URL of the source that triggered the alert")
    structured_data: Dict[str, Any] = Field(..., description="The json schema requested for the alert")
    
    model_config = ConfigDict(from_attributes=True)