import uuid
from datetime import datetime


class AgentController:
    id: uuid.UUID
    email: str
    api_key: str
    credits: int
    created_at: datetime
    last_login: datetime