import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SummarEase"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str
    
    # JWT settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Hugging Face API
    HUGGINGFACE_API_KEY: str
    
    # Redis settings
    REDIS_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()
