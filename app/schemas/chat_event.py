from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any

class ChatEvent(BaseModel):
    id: str = Field(..., description="The ID of the alert event")
    alert_chat_id: str = Field(..., description="The ID of the alert prompt")
    document_id: str = Field(..., description="The ID of the document that triggered the alert")
    triggered_at: datetime = Field(..., description="The datetime the alert event was triggered")
        
    model_config = ConfigDict(from_attributes=True)