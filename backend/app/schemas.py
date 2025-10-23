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


class FactCheckFlag(BaseModel):
    """Represents a specific claim that failed fact-checking"""
    claim: str
    verdict: str  # 'false', 'disputed', 'misleading'
    evidence_source: str
    evidence_url: Optional[str] = None
    explanation: str
    confidence: float
    claim_context: Optional[str] = None     # Surrounding sentences for transparency
    claim_location: Optional[str] = None    # "headline", "lead", "body"


class FlaggedArticle(BaseModel):
    """Article that failed fact-checking"""
    id: int
    source: str
    title: str
    url: str
    timestamp: datetime
    fact_check_status: str
    fact_check_flags: List[FactCheckFlag]
    
    class Config:
        from_attributes = True


class SourceErrorStats(BaseModel):
    """Error statistics for a news source"""
    domain: str
    flagged_count: int
    false_count: int
    disputed_count: int
    total_articles: int
    error_rate: float


class InternationalSource(BaseModel):
    """International news source"""
    domain: str
    country: str
    region: str
    political_bias: Dict[str, float]
    article_count: int


class InternationalCoverage(BaseModel):
    """International coverage analysis"""
    has_international: bool
    source_count: int
    sources: List[InternationalSource]
    regional_breakdown: Dict[str, int]
    political_distribution: Dict[str, float]
    differs_from_us: bool
    coverage_gap_score: float


class FlaggedArticlesResponse(BaseModel):
    """Response for flagged articles endpoint"""
    total: int
    limit: int
    offset: int
    articles: List[FlaggedArticle]
    source_stats: List[SourceErrorStats]
    summary: Dict[str, int]


class ArticleDetail(ArticleBase):
    id: int
    language: Optional[str] = None
    text_snippet: Optional[str] = None
    entities: Optional[List[str]] = None
    fact_check_status: Optional[str] = None
    fact_check_flags: Optional[List[FactCheckFlag]] = None

    class Config:
        from_attributes = True


# Event schemas
class EventSource(BaseModel):
    domain: str
    title: str
    url: Optional[str] = None
    political_bias: Optional[Dict[str, float]] = None  # {"left": 0.3, "center": 0.6, "right": 0.1}


class ScoringBreakdown(BaseModel):
    source_diversity: Dict[str, Any]
    geo_diversity: Dict[str, Any]
    primary_evidence: Dict[str, Any]
    official_match: Dict[str, Any]


class ConflictDetail(BaseModel):
    has_conflict: bool
    severity: str
    coherence_score: float
    embedding_similarity: Optional[float] = None
    entity_overlap: Optional[float] = None
    title_consistency: Optional[float] = None


class ArticleExcerpt(BaseModel):
    """Represents a key excerpt from an article showing perspective differences"""
    source: str
    title: str
    url: str
    excerpt: str
    relevance_score: float


class NarrativePerspective(BaseModel):
    """Represents a narrative perspective within a conflicting event"""
    sources: List[str]
    article_count: int
    representative_title: str
    key_entities: List[str]
    sentiment: str
    focus_keywords: List[str]
    political_leaning: Optional[str] = None
    representative_excerpts: Optional[List[ArticleExcerpt]] = None


class ConflictClassification(BaseModel):
    """Classification of conflict type"""
    conflict_type: str  # "numerical", "attribution", "framing", "facts", "interpretation"
    is_factual_dispute: bool
    is_framing_difference: bool
    confidence: float


class ConflictExplanation(BaseModel):
    """Explains why sources present different narratives"""
    perspectives: List[NarrativePerspective]
    key_difference: str
    difference_type: str
    classification: Optional[ConflictClassification] = None
    keyword_overlap: Optional[float] = None  # 0-1, higher = more similar perspectives


class BiasCompass(BaseModel):
    """Source bias distribution across four dimensions"""
    geographic: Dict[str, float]
    political: Dict[str, float]
    tone: Dict[str, float]
    detail: Dict[str, float]


class InternationalSourceResponse(BaseModel):
    """Represents an international news source"""
    domain: str
    country: str
    region: str
    article_count: int
    political_bias: Optional[Dict[str, float]] = None  # {"left": 0.3, "center": 0.6, "right": 0.1}


class InternationalCoverageResponse(BaseModel):
    """Coverage metrics for international sources of an event"""
    has_international: bool
    source_count: int = 0
    sources: List[InternationalSourceResponse] = []
    regional_breakdown: Dict[str, int] = {}  # {"Europe": 5, "Asia": 3}
    political_distribution: Dict[str, float] = {}  # {"left": 0.3, "center": 0.5, "right": 0.2}
    coverage_gap_score: float = 0.0  # 0-1, higher = more difference between US and international
    differs_from_us: bool = False


class EventBase(BaseModel):
    id: int
    summary: str
    articles_count: int
    unique_sources: int
    truth_score: float
    confidence_tier: str
    has_conflict: bool = False
    conflict_severity: Optional[str] = None
    conflict_explanation: Optional[ConflictExplanation] = None
    bias_compass: Optional[BiasCompass] = None
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    importance_score: Optional[float] = None  # Multi-factor importance score (0-100)
    international_coverage: Optional[InternationalCoverageResponse] = None
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
    conflict_events: int
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


# Polarizing sources schemas
class PolarizingExcerpt(BaseModel):
    """Excerpt from a polarizing news source"""
    title: str
    url: str
    summary: str
    timestamp: datetime
    polarization_score: float  # 0-100 score for this specific excerpt
    highlighted_keywords: List[str]  # Polarizing words found
    topic_tags: List[str]  # "Trump", "Congress", etc.


class PolarizingSource(BaseModel):
    """News source with polarization metrics"""
    domain: str
    polarization_score: float
    political_bias: Dict[str, float]
    tone_bias: Dict[str, float]
    article_count: int
    sample_excerpts: List[PolarizingExcerpt]


class PolarizingSourcesResponse(BaseModel):
    """Response for polarizing sources endpoint"""
    total_sources: int
    sources: List[PolarizingSource]
    methodology: str


# Error schema
class ErrorResponse(BaseModel):
    detail: str
