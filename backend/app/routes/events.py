"""Events API endpoints"""

import json
from typing import Optional

from app.config import settings
from app.db import get_db
from app.models import Article, Event
from app.schemas import (
    ArticleDetail,
    BiasCompass,
    ConflictExplanation,
    CoverageTier,
    EventDetail,
    EventList,
    EventSource,
    EventsResponse,
    FactCheckFlag,
    FlaggedArticle,
    FlaggedArticlesResponse,
    NarrativePerspective,
    ScoringBreakdown,
    SourceErrorStats,
    StatsResponse,
    TopSource,
    UnderreportedEvent,
    UnderreportedResponse,
)
from app.services.bias import BiasAnalyzer
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

router = APIRouter()

# Initialize bias analyzer for source lookups
_bias_analyzer = None


def get_bias_analyzer() -> BiasAnalyzer:
    """Lazy load bias analyzer"""
    global _bias_analyzer
    if _bias_analyzer is None:
        _bias_analyzer = BiasAnalyzer()
    return _bias_analyzer


def create_event_source_with_bias(article: Article) -> EventSource:
    """Create EventSource with political bias data"""
    bias_analyzer = get_bias_analyzer()
    bias = bias_analyzer.get_source_bias(article.source)
    
    political_bias = None
    if bias:
        political_bias = bias.political
    
    return EventSource(
        domain=article.source,
        title=article.title,
        url=article.url,
        political_bias=political_bias
    )


def deserialize_conflict_explanation(
    explanation_json: Optional[str],
) -> Optional[ConflictExplanation]:
    """
    Deserialize conflict explanation JSON to ConflictExplanation object.

    Args:
        explanation_json: JSON string of conflict explanation

    Returns:
        ConflictExplanation object or None
    """
    if not explanation_json:
        return None
    
    # Handle empty or whitespace-only strings
    if not explanation_json.strip():
        return None

    try:
        explanation_data = json.loads(explanation_json)
        
        # Validate structure
        if not isinstance(explanation_data, dict):
            print(f"Warning: conflict_explanation is not a dict: {type(explanation_data)}")
            return None
        
        # Convert perspective dicts to NarrativePerspective objects
        perspectives = []
        for p in explanation_data.get("perspectives", []):
            try:
                perspectives.append(NarrativePerspective(**p))
            except Exception as e:
                print(f"Warning: Failed to parse perspective: {e}, data: {p}")
                continue
        
        if not perspectives:
            return None
        
        return ConflictExplanation(
            perspectives=perspectives,
            key_difference=explanation_data.get("key_difference", ""),
            difference_type=explanation_data.get("difference_type", ""),
        )
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in conflict_explanation: {e}")
        print(f"  Content preview: {explanation_json[:100]}")
        return None
    except Exception as e:
        print(f"Warning: Failed to deserialize conflict explanation: {e}")
        return None


def deserialize_bias_compass(bias_json: Optional[str]) -> Optional[BiasCompass]:
    """
    Deserialize bias compass JSON to BiasCompass object.

    Args:
        bias_json: JSON string of bias compass

    Returns:
        BiasCompass object or None
    """
    if not bias_json:
        return None
    
    # Handle empty or whitespace-only strings
    if not bias_json.strip():
        return None

    try:
        bias_data = json.loads(bias_json)
        
        # Validate structure
        if not isinstance(bias_data, dict):
            print(f"Warning: bias_compass is not a dict: {type(bias_data)}")
            return None
        
        return BiasCompass(**bias_data)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in bias_compass: {e}")
        print(f"  Content preview: {bias_json[:100]}")
        return None
    except Exception as e:
        print(f"Warning: Failed to deserialize bias compass: {e}")
        return None


@router.get("", response_model=EventsResponse)
async def get_events(
    status: Optional[str] = Query("all", regex="^(confirmed|developing|all)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    underreported: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of events.

    Query parameters:
        - status: Filter by confidence tier (confirmed, developing, all)
        - limit: Results per page (1-100)
        - offset: Pagination offset
        - underreported: Filter underreported events (true/false)
    """
    query = db.query(Event)

    # Apply status filter
    if status == "confirmed":
        query = query.filter(Event.truth_score >= settings.confirmed_threshold)
    elif status == "developing":
        query = query.filter(
            and_(
                Event.truth_score >= settings.developing_threshold,
                Event.truth_score < settings.confirmed_threshold,
            )
        )
    else:  # all
        query = query.filter(Event.truth_score >= settings.developing_threshold)

    # Apply underreported filter
    if underreported is not None:
        query = query.filter(Event.underreported == underreported)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    events = (
        query.order_by(Event.truth_score.desc(), Event.first_seen.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Build response with sources
    results = []
    for event in events:
        articles = (
            db.query(Article)
            .filter(Article.cluster_id == event.id)
            .limit(10)  # Top 10 sources
            .all()
        )
        sources = [create_event_source_with_bias(a) for a in articles]

        # Deserialize conflict explanation if present
        conflict_explanation = deserialize_conflict_explanation(
            event.conflict_explanation_json
        )

        # Deserialize bias compass if present
        bias_compass = deserialize_bias_compass(event.bias_compass_json)

        event_dict = {
            "id": event.id,
            "summary": event.summary,
            "articles_count": event.articles_count,
            "unique_sources": event.unique_sources,
            "truth_score": event.truth_score,
            "confidence_tier": event.confidence_tier,
            "underreported": event.underreported,
            "coherence_score": event.coherence_score,
            "has_conflict": event.has_conflict,
            "conflict_severity": event.conflict_severity,
            "conflict_explanation": conflict_explanation,
            "bias_compass": bias_compass,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
        }
        results.append(EventList(**event_dict))

    return EventsResponse(total=total, limit=limit, offset=offset, results=results)


# Note: Specific routes must come before /{event_id} to avoid path conflicts
@router.get("/underreported", response_model=UnderreportedResponse)
async def get_underreported_events(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get events flagged as underreported.

    These are events with NGO/Gov sources but lacking major wire coverage.
    """
    query = db.query(Event).filter(Event.underreported == True)

    total = query.count()

    events = query.order_by(Event.first_seen.desc()).limit(limit).offset(offset).all()

    results = []
    for event in events:
        articles = db.query(Article).filter(Article.cluster_id == event.id).limit(10).all()
        sources = [create_event_source_with_bias(a) for a in articles]

        # Generate underreported reason
        has_ngo = any(
            any(official in a.source.lower() for official in settings.official_sources)
            for a in articles
        )

        reason = (
            f"Present in {'NGO/Gov sources' if has_ngo else 'small/local sources'}, "
            f"absent from major wire services for {settings.underreported_window_hours}+ hours"
        )

        event_dict = {
            "id": event.id,
            "summary": event.summary,
            "articles_count": event.articles_count,
            "unique_sources": event.unique_sources,
            "truth_score": event.truth_score,
            "confidence_tier": event.confidence_tier,
            "underreported": event.underreported,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
            "reason": reason,
        }
        results.append(UnderreportedEvent(**event_dict))

    return UnderreportedResponse(total=total, limit=limit, offset=offset, results=results)


@router.get("/conflicts", response_model=EventsResponse)
async def get_conflict_events(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get events with narrative conflicts (coherence < 80).

    These are events where sources present significantly different stories.
    Only includes political and social events (filters out natural disasters, sports).
    """
    # Filter for conflicts, excluding natural disasters and irrelevant categories
    query = (
        db.query(Event)
        .filter(Event.has_conflict == True)
        .filter(
            (Event.category != 'natural_disaster') | (Event.category == None)
        )
    )

    total = query.count()

    events = (
        query.order_by(Event.coherence_score.asc(), Event.first_seen.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Build response with sources
    results = []
    for event in events:
        articles = (
            db.query(Article)
            .filter(Article.cluster_id == event.id)
            .limit(10)  # Top 10 sources
            .all()
        )
        sources = [create_event_source_with_bias(a) for a in articles]

        # Deserialize conflict explanation if present
        conflict_explanation = deserialize_conflict_explanation(
            event.conflict_explanation_json
        )

        # Deserialize bias compass if present
        bias_compass = deserialize_bias_compass(event.bias_compass_json)

        event_dict = {
            "id": event.id,
            "summary": event.summary,
            "articles_count": event.articles_count,
            "unique_sources": event.unique_sources,
            "truth_score": event.truth_score,
            "confidence_tier": event.confidence_tier,
            "underreported": event.underreported,
            "coherence_score": event.coherence_score,
            "has_conflict": event.has_conflict,
            "conflict_severity": event.conflict_severity,
            "conflict_explanation": conflict_explanation,
            "bias_compass": bias_compass,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
        }
        results.append(EventList(**event_dict))

    return EventsResponse(total=total, limit=limit, offset=offset, results=results)


@router.get("/stats/summary", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """
    Get aggregate statistics.

    Returns counts, averages, and top sources.
    """
    total_events = db.query(func.count(Event.id)).scalar() or 0
    total_articles = db.query(func.count(Article.id)).scalar() or 0

    confirmed = (
        db.query(func.count(Event.id))
        .filter(Event.truth_score >= settings.confirmed_threshold)
        .scalar()
        or 0
    )

    developing = (
        db.query(func.count(Event.id))
        .filter(
            and_(
                Event.truth_score >= settings.developing_threshold,
                Event.truth_score < settings.confirmed_threshold,
            )
        )
        .scalar()
        or 0
    )

    unverified = (
        db.query(func.count(Event.id))
        .filter(Event.truth_score < settings.developing_threshold)
        .scalar()
        or 0
    )

    underreported_count = (
        db.query(func.count(Event.id)).filter(Event.underreported == True).scalar() or 0
    )

    conflict_count = (
        db.query(func.count(Event.id)).filter(Event.has_conflict == True).scalar() or 0
    )

    avg_score = db.query(func.avg(Event.truth_score)).scalar() or 0.0
    avg_coherence = db.query(func.avg(Event.coherence_score)).scalar() or 0.0

    # Get last ingestion time
    last_article = db.query(Article).order_by(Article.ingested_at.desc()).first()
    last_ingestion = last_article.ingested_at if last_article else None

    # Get unique sources count
    sources_count = db.query(func.count(func.distinct(Article.source))).scalar() or 0

    # Get top sources
    top_sources_raw = (
        db.query(Article.source, func.count(Article.id).label("count"))
        .group_by(Article.source)
        .order_by(func.count(Article.id).desc())
        .limit(10)
        .all()
    )
    top_sources = [TopSource(domain=s[0], article_count=s[1]) for s in top_sources_raw]

    return StatsResponse(
        total_events=total_events,
        total_articles=total_articles,
        confirmed_events=confirmed,
        developing_events=developing,
        underreported_events=underreported_count,
        conflict_events=conflict_count,
        avg_confidence_score=round(avg_score, 2),
        avg_coherence_score=round(avg_coherence, 2),
        last_ingestion=last_ingestion,
        sources_count=sources_count,
        coverage_by_tier=CoverageTier(
            confirmed=confirmed, developing=developing, unverified=unverified
        ),
        top_sources=top_sources,
    )


@router.get("/flagged", response_model=FlaggedArticlesResponse)
async def get_flagged_articles(
    severity: Optional[str] = Query("all", regex="^(false|disputed|all)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get articles that failed fact-checks.
    
    Query parameters:
        - severity: Filter by fact-check status (false, disputed, all)
        - limit: Results per page (1-100)
        - offset: Pagination offset
        - source: Filter by specific source domain
        - days: Time range in days (1-365)
    """
    from datetime import datetime, timedelta
    from app.services.fact_check_analytics import (
        calculate_source_error_rates,
        get_flagged_summary,
    )
    
    # Date range filter
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(Article).filter(Article.timestamp >= cutoff)
    
    # Severity filter
    if severity == "false":
        query = query.filter(Article.fact_check_status == "false")
    elif severity == "disputed":
        query = query.filter(Article.fact_check_status == "disputed")
    else:  # all
        query = query.filter(
            Article.fact_check_status.in_(["false", "disputed"])
        )
    
    # Source filter
    if source:
        query = query.filter(Article.source == source)
    
    # Get total count
    total = query.count()
    
    # Get paginated articles
    articles = (
        query.order_by(Article.timestamp.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    # Build flagged article objects
    flagged_articles = []
    for article in articles:
        # Deserialize fact-check flags
        flags = []
        if article.fact_check_flags_json:
            try:
                flags_data = json.loads(article.fact_check_flags_json)
                flags = [FactCheckFlag(**f) for f in flags_data]
            except Exception as e:
                print(f"Warning: Failed to deserialize flags for article {article.id}: {e}")
        
        flagged_articles.append(
            FlaggedArticle(
                id=article.id,
                source=article.source,
                title=article.title,
                url=article.url,
                timestamp=article.timestamp,
                fact_check_status=article.fact_check_status or "unverified",
                fact_check_flags=flags,
            )
        )
    
    # Calculate source error rates
    source_stats = calculate_source_error_rates(db, days)
    
    # Get summary statistics
    summary = get_flagged_summary(db, days)
    
    return FlaggedArticlesResponse(
        total=total,
        limit=limit,
        offset=offset,
        articles=flagged_articles,
        source_stats=[SourceErrorStats(**s) for s in source_stats],
        summary=summary,
    )


@router.get("/{event_id}", response_model=EventDetail)
async def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific event.

    Includes:
        - All associated articles
        - Scoring breakdown
        - Full metadata
    """
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found")

    # Get all articles for this event
    articles = (
        db.query(Article)
        .filter(Article.cluster_id == event.id)
        .order_by(Article.timestamp.desc())
        .all()
    )

    articles_detail = []
    for a in articles:
        entities = json.loads(a.entities_json) if a.entities_json else []

        # Deserialize fact-check flags
        fact_check_flags = None
        if a.fact_check_flags_json:
            try:
                flags_data = json.loads(a.fact_check_flags_json)
                fact_check_flags = [FactCheckFlag(**f) for f in flags_data]
            except Exception as e:
                print(f"Warning: Failed to deserialize fact-check flags: {e}")

        articles_detail.append(
            ArticleDetail(
                id=a.id,
                source=a.source,
                title=a.title,
                url=a.url,
                timestamp=a.timestamp,
                summary=a.summary,
                language=a.language,
                text_snippet=a.text_snippet,
                entities=entities,
                fact_check_status=a.fact_check_status,
                fact_check_flags=fact_check_flags,
            )
        )

    # Calculate scoring breakdown
    source_score = min(event.unique_sources / 5.0, 1.0) * 25
    geo_score = (event.geo_diversity or 0) * 40
    evidence_score = 20.0 if event.evidence_flag else 0.0
    official_score = event.truth_score - source_score - geo_score - evidence_score

    scoring_breakdown = ScoringBreakdown(
        source_diversity={
            "value": round(source_score, 2),
            "weight": 0.25,
            "explanation": f"{event.unique_sources} unique sources",
        },
        geo_diversity={
            "value": round(geo_score, 2),
            "weight": 0.40,
            "explanation": f"Geographic diversity: {event.geo_diversity:.2f}"
            if event.geo_diversity
            else "No data",
        },
        primary_evidence={
            "value": round(evidence_score, 2),
            "weight": 0.20,
            "explanation": "Official source present"
            if event.evidence_flag
            else "No official source",
        },
        official_match={
            "value": round(official_score, 2),
            "weight": 0.15,
            "explanation": "Matches official feed" if event.official_match else "No official match",
        },
    )

    languages = json.loads(event.languages_json) if event.languages_json else []

    # Deserialize conflict explanation if present
    conflict_explanation = deserialize_conflict_explanation(event.conflict_explanation_json)

    # Deserialize bias compass if present
    bias_compass = deserialize_bias_compass(event.bias_compass_json)

    return EventDetail(
        id=event.id,
        summary=event.summary,
        articles_count=event.articles_count,
        unique_sources=event.unique_sources,
        geo_diversity=event.geo_diversity,
        evidence_flag=event.evidence_flag,
        official_match=event.official_match,
        truth_score=event.truth_score,
        confidence_tier=event.confidence_tier,
        underreported=event.underreported,
        coherence_score=event.coherence_score,
        has_conflict=event.has_conflict,
        conflict_severity=event.conflict_severity,
        conflict_explanation=conflict_explanation,
        bias_compass=bias_compass,
        first_seen=event.first_seen,
        last_seen=event.last_seen,
        languages=languages,
        articles=articles_detail,
        scoring_breakdown=scoring_breakdown,
    )
