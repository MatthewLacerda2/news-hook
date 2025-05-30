from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "News Hook"
    
    SECRET_KEY: str = "your-secret-key-here"  # TODO: Change this in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str    
    GEMINI_API_KEY: str
    
    DATABASE_URL: str  # This is required now, not Optional
    SQLALCHEMY_DATABASE_URI: str = None  # This will be set from DATABASE_URL
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        # Always use DATABASE_URL
        return info.data.get("DATABASE_URL")
    
    model_config = ConfigDict(
        case_sensitive=True, 
        env_file=".env",
        env_file_encoding='utf-8'
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()