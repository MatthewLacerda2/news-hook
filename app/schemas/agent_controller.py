from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

class AgentControllerBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class OAuth2Request(BaseModel):
    access_token: str

class AgentControllerResponse(AgentControllerBase):
    id: UUID
    google_id: str
    api_key: str
    credits: int

    class Config:
        from_attributes = True

# Schema for token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: datetime
    agent_controller: AgentControllerResponse
