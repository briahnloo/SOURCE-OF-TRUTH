"""Pydantic schemas for API request/response models"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


# Article schemas
class ArticleBase(BaseModel):
    source: str
    title: str
    url: str
    timestamp: datetime
    summary: Optional[str] = None


class ArticleDetail(ArticleBase):
    id: int
    language: Optional[str] = None
    text_snippet: Optional[str] = None
    entities: Optional[List[str]] = None

    class Config:
        from_attributes = True


# Event schemas
class EventSource(BaseModel):
    domain: str
    title: str
    url: Optional[str] = None


class ScoringBreakdown(BaseModel):
    source_diversity: Dict[str, Any]
    geo_diversity: Dict[str, Any]
    primary_evidence: Dict[str, Any]
    official_match: Dict[str, Any]


class EventBase(BaseModel):
    id: int
    summary: str
    articles_count: int
    unique_sources: int
    truth_score: float
    confidence_tier: str
    underreported: bool
    first_seen: datetime
    last_seen: datetime


class EventList(EventBase):
    """Event summary for list views"""

    sources: Optional[List[EventSource]] = None

    class Config:
        from_attributes = True


class EventDetail(EventBase):
    """Detailed event with all articles and scoring breakdown"""

    geo_diversity: Optional[float]
    evidence_flag: bool
    official_match: bool
    languages: Optional[List[str]] = None
    articles: List[ArticleDetail] = []
    scoring_breakdown: Optional[ScoringBreakdown] = None

    class Config:
        from_attributes = True


# Response schemas
class EventsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[EventList]


class UnderreportedEvent(EventList):
    reason: str


class UnderreportedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[UnderreportedEvent]


# Statistics schemas
class CoverageTier(BaseModel):
    confirmed: int
    developing: int
    unverified: int


class TopSource(BaseModel):
    domain: str
    article_count: int


class StatsResponse(BaseModel):
    total_events: int
    total_articles: int
    confirmed_events: int
    developing_events: int
    underreported_events: int
    avg_confidence_score: float
    last_ingestion: Optional[datetime]
    sources_count: int
    coverage_by_tier: CoverageTier
    top_sources: List[TopSource]


# Health schema
class HealthResponse(BaseModel):
    status: str
    database: str
    worker_last_run: Optional[datetime]
    total_events: int
    total_articles: int


# Error schema
class ErrorResponse(BaseModel):
    detail: str
