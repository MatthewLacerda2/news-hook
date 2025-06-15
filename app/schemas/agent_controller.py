from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

class AgentControllerBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    google_id: str = Field(..., description="Google's unique user ID")

class OAuth2Request(BaseModel):
    access_token: str = Field(..., description="Google OAuth2 access token")

class AgentControllerResponse(AgentControllerBase):
    id: str
    api_key: str = Field(..., description="API key for authentication")
    credit_balance: float = Field(default=10, description="Credits. In cents of USD")
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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
