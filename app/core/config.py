from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):

    DATABASE_URL: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_REDIRECT_URI: str
    
    SECRET_KEY: str
    
    TELEGRAM_BOT_TOKEN: str
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "News Hook"
    
    model_config = ConfigDict(
        case_sensitive=True, 
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()