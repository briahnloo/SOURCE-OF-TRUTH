"""Configuration management"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database (supports both SQLite and PostgreSQL)
    database_url: str = Field(
        default="sqlite:////data/app.db",
        description="Database connection URL. Use postgresql:// for production."
    )

    # API Keys (optional)
    newsapi_key: str = ""
    mediastack_key: str = ""

    # Monitoring
    discord_webhook_url: str = ""

    # CORS - just use a simple list with a default
    allowed_origins_str: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins_str.split(",")]

    # Scoring thresholds
    confirmed_threshold: float = 75.0
    developing_threshold: float = 40.0

    # Clustering parameters
    dbscan_eps: float = 0.3
    dbscan_min_samples: int = 3
    clustering_window_hours: int = 24

    # Underreported detection
    underreported_window_hours: int = 48
    underreported_min_sources: int = 2

    # Data retention
    article_retention_days: int = 30

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Official sources (for evidence scoring)
    official_sources: List[str] = [
        "usgs.gov",
        "who.int",
        "nasa.gov",
        "unocha.org",
        "reliefweb.int",
    ]

    # Major wire services (for underreported detection)
    major_wires: List[str] = [
        "ap.org",
        "reuters.com",
        "afp.com",
    ]


settings = Settings()
