"""Events API endpoints"""

import json
from typing import Optional

from app.config import settings
from app.db import get_db
from app.models import Article, Event
from app.schemas import (
    ArticleDetail,
    CoverageTier,
    EventDetail,
    EventList,
    EventSource,
    EventsResponse,
    ScoringBreakdown,
    StatsResponse,
    TopSource,
    UnderreportedEvent,
    UnderreportedResponse,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

router = APIRouter()


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
        sources = [EventSource(domain=a.source, title=a.title, url=a.url) for a in articles]

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
        sources = [EventSource(domain=a.source, title=a.title, url=a.url) for a in articles]

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

    avg_score = db.query(func.avg(Event.truth_score)).scalar() or 0.0

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
        avg_confidence_score=round(avg_score, 2),
        last_ingestion=last_ingestion,
        sources_count=sources_count,
        coverage_by_tier=CoverageTier(
            confirmed=confirmed, developing=developing, unverified=unverified
        ),
        top_sources=top_sources,
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
        first_seen=event.first_seen,
        last_seen=event.last_seen,
        languages=languages,
        articles=articles_detail,
        scoring_breakdown=scoring_breakdown,
    )
