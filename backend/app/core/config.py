from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database — REQUIRED: must be set via .env or environment variable
    DATABASE_URL: str
    
    # Storage
    STORAGE_PATH: str = "./storage"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Model
    MODEL_PATH: str = "./storage/models/best.pt"
    CONF_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    
    # Reliability & Limits
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB default
    DETECT_TIMEOUT_SECONDS: int = 30
    DETECT_MAX_CONCURRENCY: int = 2

    # Feature Flags
    # Set TKPI_FUZZY_SEARCH=false in .env to disable token-based fuzzy search
    TKPI_FUZZY_SEARCH: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
