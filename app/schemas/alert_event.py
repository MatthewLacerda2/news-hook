from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime
from pydantic import Field
from typing import Dict, JsonPrimitive


class AlertEventResponse(Base):

    id: UUID = Field(..., description="The ID of the alert event")
    alert_prompt_id: UUID = Field(..., description="The ID of the alert prompt")
    triggered_at: datetime = Field(..., description="The datetime the alert event was triggered")
    
    output: str = Field(..., description="The LLM output on the matter")
    tags: list[str] = Field(..., description="The tags for the alert")
    structured_data: Dict[str, JsonPrimitive] = Field(..., description="The structured JSON response as requested by the alert requester")