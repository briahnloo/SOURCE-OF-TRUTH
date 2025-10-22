"""Configuration management"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database (supports both SQLite and PostgreSQL)
    database_url: str = Field(
        default="sqlite:////data/app.db",
        description="Database connection URL. Use postgresql:// for production."
    )

    # API Keys (optional)
    newsapi_key: str = ""
    mediastack_key: str = ""
    google_factcheck_api_key: str = ""

    # Monitoring
    discord_webhook_url: str = ""

    # CORS - just use a simple list with a default
    allowed_origins_str: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins_str.split(",")]

    # Scoring thresholds (category-specific)
    confirmed_threshold: float = 60.0  # For politics/international
    confirmed_threshold_scientific: float = 75.0  # For natural_disaster/health
    developing_threshold: float = 40.0

    # Clustering parameters
    dbscan_eps: float = 0.3
    dbscan_min_samples: int = 3
    clustering_window_hours: int = 24

    # Data retention
    article_retention_days: int = 30

    # Ingestion scheduling - LEGACY (for backward compatibility with old scheduler)
    # TODO: Switch to tiered_scheduler.py once deployed
    ingestion_interval_peak: int = 15  # minutes during peak hours
    ingestion_interval_offpeak: int = 30  # minutes during off-peak hours

    # Ingestion scheduling - Tiered Pipeline (for new system)
    # TIER 1: Fast ingestion (critical sources only)
    tier1_interval_peak: int = 10  # minutes, GDELT only
    tier1_interval_offpeak: int = 20  # minutes off-peak

    # TIER 2: Standard ingestion (main sources)
    tier2_interval_peak: int = 15  # minutes
    tier2_interval_offpeak: int = 30  # minutes

    # TIER 3: Analysis pipeline (embeddings, coherence)
    tier3_interval: int = 60  # once per hour (all hours)

    # TIER 4: Deep analysis (fact-checking, importance)
    tier4_interval: int = 240  # every 4 hours

    # Peak hour definition
    peak_hours_start: int = 6  # 6 AM
    peak_hours_end: int = 23  # 11 PM

    # Performance optimization
    enable_parallel_fetching: bool = True
    max_fact_check_workers: int = 2  # reduced from 3
    fact_check_batch_size: int = 30  # reduced from 50, fact-check every 4h so lower per-run

    # Intelligent batching
    max_excerpts_per_run: int = 8  # down from 10/15
    max_articles_for_analysis: int = 100  # cap memory usage
    conflict_reevaluation_hours: int = 6  # down from 48 (most resolved by then)

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


settings = Settings()
