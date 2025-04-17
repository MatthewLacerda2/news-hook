from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

class AgentControllerBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    google_id: str = Field(..., description="Google's unique user ID")

class OAuth2Request(BaseModel):
    access_token: str = Field(..., description="Google OAuth2 access token")

class AgentControllerResponse(AgentControllerBase):
    id: UUID
    api_keys: str = Field(..., description="API key for authentication")
    credits: int = Field(default=0, description="Number of credits available")
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for token response
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")
    expires_in: datetime = Field(..., description="Token expiration time")
    agent_controller: AgentControllerResponse

    @field_validator('token_type')
    @classmethod
    def validate_token_type(cls, v: str) -> str:
        if v.lower() != 'bearer':
            raise ValueError('token_type must be bearer')
        return v.lower()
