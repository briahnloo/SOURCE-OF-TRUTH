"""SQLAlchemy database models"""

from datetime import datetime

from app.db import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func


class Article(Base):
    """Raw article model (30-day retention)"""

    __tablename__ = "articles_raw"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    language = Column(String(10))
    summary = Column(Text)
    text_snippet = Column(Text)
    entities_json = Column(Text)  # JSON string: ["entity1", "entity2"]
    cluster_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, source={self.source}, title={self.title[:50]})>"


class Event(Base):
    """Aggregated event model (indefinite retention)"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text, nullable=False)
    articles_count = Column(Integer, nullable=False)
    unique_sources = Column(Integer, nullable=False)
    geo_diversity = Column(Float, nullable=True)
    evidence_flag = Column(Boolean, default=False, nullable=False)
    official_match = Column(Boolean, default=False, nullable=False)
    truth_score = Column(Float, nullable=False, index=True)
    underreported = Column(Boolean, default=False, nullable=False, index=True)
    first_seen = Column(DateTime, nullable=False, index=True)
    last_seen = Column(DateTime, nullable=False)
    languages_json = Column(Text)  # JSON string: ["en", "es"]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, score={self.truth_score}, summary={self.summary[:50]})>"

    @property
    def confidence_tier(self) -> str:
        """Get confidence tier based on truth score"""
        if self.truth_score >= 75:
            return "confirmed"
        elif self.truth_score >= 40:
            return "developing"
        else:
            return "unverified"
