"""Events API endpoints"""

from typing import Optional

from app.config import settings
from app.core.json_utils import parse_json_body, parse_json_list, safe_json_loads
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
from app.services.service_registry import get_bias_analyzer
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

router = APIRouter()


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

    # Apply status filter with category-specific thresholds
    if status == "confirmed":
        # Category-specific confirmed threshold
        query = query.filter(
            or_(
                and_(
                    Event.category.in_(['natural_disaster', 'health']),
                    Event.truth_score >= settings.confirmed_threshold_scientific
                ),
                and_(
                    or_(
                        Event.category.in_(['politics', 'international', 'crime', 'other']),
                        Event.category == None
                    ),
                    Event.truth_score >= settings.confirmed_threshold
                )
            )
        )
    elif status == "developing":
        # Developing: between 40 and category-specific confirmed threshold
        query = query.filter(
            and_(
                Event.truth_score >= settings.developing_threshold,
                or_(
                    and_(
                        Event.category.in_(['natural_disaster', 'health']),
                        Event.truth_score < settings.confirmed_threshold_scientific
                    ),
                    and_(
                        or_(
                            Event.category.in_(['politics', 'international', 'crime', 'other']),
                            Event.category == None
                        ),
                        Event.truth_score < settings.confirmed_threshold
                    )
                )
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

        # Deserialize conflict explanation and bias compass
        conflict_explanation = parse_json_body(
            event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
        )
        bias_compass = parse_json_body(
            event.bias_compass_json, BiasCompass, "bias_compass"
        )

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
    Get events with MEANINGFUL political narrative conflicts.
    
    ONLY includes:
    - US politics
    - International conflicts (Gaza, Ukraine, etc.)
    
    Requirements:
    - Coherence < 70 (medium or high severity)
    - At least 6 articles from 4+ sources
    - Left AND right coverage
    - Keyword overlap < 40% (genuine differences, not just headline variations)
    """
    # Filter for POLITICAL conflicts only
    query = (
        db.query(Event)
        .filter(Event.has_conflict == True)
        .filter(Event.coherence_score < 70)  # Medium or high severity
        .filter(Event.articles_count >= 6)    # Minimum coverage
        .filter(Event.unique_sources >= 4)    # Source diversity
        .filter(Event.conflict_explanation_json != None)  # Has perspectives
        .filter(
            # ONLY politics and international (or NULL for uncategorized)
            (Event.category.in_(['politics', 'international'])) | (Event.category == None)
        )
    )

    total_candidates = query.count()

    # Get more events than needed to filter for political diversity
    events = (
        query.order_by(Event.last_seen.desc())
        .limit(limit * 3)  # Get 3x to account for filtering
        .offset(offset)
        .all()
    )

    # ADDITIONAL FILTER: Check for political diversity in results
    results = []
    for event in events:
        articles = (
            db.query(Article)
            .filter(Article.cluster_id == event.id)
            .limit(10)
            .all()
        )
        
        # Filter out non-political topics by content (regardless of category)
        summary_lower = event.summary.lower()
        skip_event = False
        
        # Foreign elections (not US politics)
        foreign_election_patterns = [
            ('japan', 'prime minister'),
            ('japan', 'pm'),
            ('bolivia', 'president'),
            ('bolivia', 'election'),
        ]
        is_foreign_election = any(
            all(kw in summary_lower for kw in pattern) 
            for pattern in foreign_election_patterns
        )
        if is_foreign_election:
            continue  # Skip - foreign election, not US politics
        
        # Non-political topics
        non_political_topics = [
            'louvre', 'museum heist', 'jewelry',
            'aws outage', 'amazon', 'internet outage',
            'nfl', 'sports', 'playoffs',
        ]
        if any(topic in summary_lower for topic in non_political_topics):
            continue  # Skip - not political
        
        # Parse conflict explanation
        conflict_explanation = parse_json_body(
            event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
        )
        
        # Skip if no real political diversity in perspectives
        if conflict_explanation:
            perspectives = conflict_explanation.perspectives
            political_leanings = set()
            
            # Extract political leanings from perspectives
            for p in perspectives:
                # Perspectives are NarrativePerspective objects
                if hasattr(p, 'political_leaning') and p.political_leaning:
                    political_leanings.add(p.political_leaning)
            
            # Require at least 2 different political leanings
            if len(political_leanings) < 2:
                continue  # Skip - not politically diverse
            
            # REQUIRE left AND right coverage for true conflict
            if 'left' not in political_leanings or 'right' not in political_leanings:
                # Only show if coherence is VERY low (major disagreement)
                if event.coherence_score >= 40:
                    continue  # Skip - not severe enough without left+right
            
            # Check keyword overlap - CRITICAL FILTER
            # Note: keyword_overlap may be None for older events (not yet recalculated)
            keyword_overlap = conflict_explanation.keyword_overlap
            if keyword_overlap is not None and keyword_overlap >= 0.40:
                # 40%+ overlap = same story
                continue  # Skip - perspectives too similar
            
            # Check classification if available
            classification = conflict_explanation.classification
            if classification:
                # Classification is a Pydantic object
                if (classification.conflict_type == 'interpretation' and 
                    classification.confidence < 0.6):
                    continue  # Skip - not meaningful difference
        else:
            continue  # Skip events without explanation
        
        # Event passes filters - include it
        sources = [create_event_source_with_bias(a) for a in articles]
        bias_compass = parse_json_body(event.bias_compass_json, BiasCompass, "bias_compass")
        
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
        
        # Stop if we have enough results
        if len(results) >= limit:
            break
    
    return EventsResponse(total=len(results), limit=limit, offset=offset, results=results)


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
        flags = parse_json_list(
            article.fact_check_flags_json, FactCheckFlag, "fact_check_flags"
        )

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
        # Deserialize entities and fact-check flags
        entities = safe_json_loads(a.entities_json, default=[])
        fact_check_flags = parse_json_list(
            a.fact_check_flags_json, FactCheckFlag, "fact_check_flags"
        )

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

    # Deserialize languages, conflict explanation, and bias compass
    languages = safe_json_loads(event.languages_json, default=[])
    conflict_explanation = parse_json_body(
        event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
    )
    bias_compass = parse_json_body(
        event.bias_compass_json, BiasCompass, "bias_compass"
    )

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
