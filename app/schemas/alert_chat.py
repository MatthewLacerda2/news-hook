from pydantic import BaseModel
from datetime import datetime

class AlertChatItem(BaseModel):
    expires_at: datetime
    prompt: str