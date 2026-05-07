import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "CV Optimizer AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # AI Keys
    GOOGLE_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_ME_FOR_PRODUCTION"
    ALGORITHM: str = "HS256"

    # Access token: short-lived (15 min default, 1 day max)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Refresh token: long-lived, stored as HttpOnly cookie
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Environment: "development" | "production"
    # In development the refresh cookie is sent without Secure flag so it
    # works over plain HTTP (localhost). In production Secure=True is set.
    ENVIRONMENT: str = "development"

    # Cookie name for the refresh token
    REFRESH_COOKIE_NAME: str = "refresh_token"

    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cv_optimizer"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Storage
    CHROMA_DB_DIR: str = "data/chroma_db"
    UPLOAD_DIR: str = "data/uploads"

    @property
    def get_database_uri(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

# Ensure directories exist
os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)