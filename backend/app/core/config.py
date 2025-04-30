from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "SummarEase"
    API_V1_STR: str = "/api/v1"

    # Domain settings (for OAuth redirects)
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost"

    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db"  # Local SQLite database for development

    # JWT settings
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = "222905126636-uc3r7knd5c603iob9np69qlgdt7nsqbv.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "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"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    GOOGLE_SCOPES: str = "email profile"

    # Cohere API
    COHERE_API_KEY: str = "Kz7rbTizHN8Gq66pWdDKUXR7igH8bfmmg0FAM1wf"
    
    # Legacy API keys (kept for backward compatibility)
    HUGGINGFACE_API_KEY: Optional[str] = None

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Development settings
    PROCESS_DIRECTLY: bool = True

    # Scaling settings
    MAX_WORKERS: int = 4
    RATE_LIMIT_PER_MINUTE: int = 20

    # Initial user credits
    DEFAULT_CREDITS: int = 10

    # AWS settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
