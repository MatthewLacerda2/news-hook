import uuid
from datetime import datetime
from enum import Enum

class UserTier(Enum):
    FREE = "free"
    PAID = "paid"

class AgentController:
    id: uuid.UUID
    email: str
    plan: str
    credits: int
    api_key: str
    tier: UserTier
    created_at: datetime
    last_login: datetime
    usage_quota: int
    usage_count: int
