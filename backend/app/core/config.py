"""Application configuration settings."""
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database - can be a URL or JSON from AWS Secrets Manager
    DATABASE_URL: str = "postgresql://admin:secret@db:5432/appdb"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def parse_database_url(cls, v: str) -> str:
        """Parse DATABASE_URL from JSON if it's an RDS secret."""
        if not v:
            return v
        v = v.strip()
        if v.startswith("{"):
            try:
                secret = json.loads(v)
                username = secret.get("username", "")
                password = secret.get("password", "")
                host = secret.get("host", "")
                port = secret.get("port", 5432)
                dbname = secret.get("dbname", "")
                return f"postgresql://{username}:{password}@{host}:{port}/{dbname}"
            except json.JSONDecodeError:
                pass
        return v

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"  # development, preprod, prod

    # API
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "{{PROJECT_NAME}}"
    VERSION: str = "0.1.0"

    # Build info (set at build time via environment variables)
    GIT_SHA: str = "unknown"
    BUILD_TIMESTAMP: str = "unknown"

    # CORS - comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Cognito authentication
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_CLIENT_ID: Optional[str] = None
    COGNITO_REGION: str = "us-east-1"
    COGNITO_DOMAIN: Optional[str] = None

    # E2E Test mode - allows test auth bypass in development
    # NEVER enable in production
    E2E_TEST_MODE: bool = False

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def auth_enabled(self) -> bool:
        """Check if authentication is configured."""
        return bool(self.COGNITO_USER_POOL_ID and self.COGNITO_CLIENT_ID)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "prod"

    @model_validator(mode="after")
    def validate_production_config(self) -> "Settings":
        """Ensure secure configuration in production environments."""
        if self.ENVIRONMENT in ("prod", "preprod"):
            if "admin:secret@" in self.DATABASE_URL:
                raise ValueError(
                    "Default database credentials cannot be used in production. "
                    "Set DATABASE_URL environment variable with secure credentials."
                )
            if self.DEBUG:
                raise ValueError(
                    "DEBUG mode cannot be enabled in production. "
                    "Set DEBUG=false in production environments."
                )
            if self.E2E_TEST_MODE:
                raise ValueError(
                    "E2E_TEST_MODE cannot be enabled in production. "
                    "This is a security risk."
                )
        return self

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
