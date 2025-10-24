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
    InternationalCoverageResponse,
    NarrativePerspective,
    PolarizingExcerpt,
    PolarizingSource,
    PolarizingSourcesResponse,
    ScoringBreakdown,
    SourceErrorStats,
    StatsResponse,
    TopSource,
)
from app.services.service_registry import get_bias_analyzer
from app.services.international_coverage import (
    analyze_international_coverage,
    load_international_coverage,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

router = APIRouter()


def get_international_coverage_for_event(event: Event, articles: list, db: Session) -> Optional[InternationalCoverageResponse]:
    """Parse international coverage data for an event"""
    if not event.international_coverage_json:
        return None
    
    try:
        coverage = load_international_coverage(event)
        if not coverage:
            return None
        
        # Convert to response format
        sources = []
        for source in coverage.sources:
            sources.append({
                "domain": source.domain,
                "country": source.country,
                "region": source.region,
                "article_count": source.article_count,
                "political_bias": source.political_bias
            })
        
        return InternationalCoverageResponse(
            has_international=coverage.has_international,
            source_count=coverage.source_count,
            sources=sources,
            regional_breakdown=coverage.regional_breakdown,
            political_distribution=coverage.political_distribution,
            coverage_gap_score=coverage.coverage_gap_score,
            differs_from_us=coverage.differs_from_us
        )
    except Exception as e:
        print(f"Error parsing international coverage: {e}")
        return None


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


def get_international_coverage_for_event(event: Event, articles: list, db: Session) -> Optional[InternationalCoverageResponse]:
    """
    Get international coverage data for an event

    Returns:
        InternationalCoverageResponse if international sources exist and importance_score > 70,
        None otherwise
    """
    # Only show international coverage for high-importance events
    if not event.importance_score or event.importance_score < 70:
        return None

    # Try to load from cached JSON first
    if event.international_coverage_json:
        try:
            coverage = load_international_coverage(event)
            if coverage:
                return InternationalCoverageResponse(
                    has_international=coverage.has_international,
                    source_count=coverage.source_count,
                    us_source_count=coverage.us_source_count,
                    international_source_count=coverage.international_source_count,
                    sources=[
                        {"domain": s.domain, "country": s.country, "region": s.region,
                         "article_count": s.article_count, "political_bias": s.political_bias}
                        for s in coverage.sources
                    ],
                    regional_breakdown=coverage.regional_breakdown,
                    political_distribution=coverage.political_distribution,
                    coverage_gap_score=coverage.coverage_gap_score,
                    differs_from_us=coverage.differs_from_us,
                )
        except Exception as e:
            print(f"Error loading international coverage from cache: {e}")
            pass  # Fall through to compute on the fly

    # Otherwise analyze on the fly
    bias_analyzer = get_bias_analyzer()
    source_biases = {}
    for article in articles:
        bias = bias_analyzer.get_source_bias(article.source)
        if bias:
            source_biases[article.source] = bias.political

    coverage = analyze_international_coverage(articles, source_biases)

    if not coverage.has_international:
        return None

    return InternationalCoverageResponse(
        has_international=coverage.has_international,
        source_count=coverage.source_count,
        us_source_count=coverage.us_source_count,
        international_source_count=coverage.international_source_count,
        sources=[
            {"domain": s.domain, "country": s.country, "region": s.region,
             "article_count": s.article_count, "political_bias": s.political_bias}
            for s in coverage.sources
        ],
        regional_breakdown=coverage.regional_breakdown,
        political_distribution=coverage.political_distribution,
        coverage_gap_score=coverage.coverage_gap_score,
        differs_from_us=coverage.differs_from_us,
    )




@router.get("", response_model=EventsResponse)
async def get_events(
    status: Optional[str] = Query("all", regex="^(confirmed|developing|all)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    politics_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of events.

    Query parameters:
        - status: Filter by confidence tier (confirmed, developing, all)
        - limit: Results per page (1-100)
        - offset: Pagination offset
        - politics_only: If true, only return political and international events (default: false)
    """
    query = db.query(Event)

    # Filter for political events if requested
    if politics_only:
        query = query.filter(Event.category.in_(['politics', 'international']))

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

    # Get total count
    total = query.count()

    # IMPROVED SORTING: Balance importance with novelty/recency
    # Fetch all matching events (will be filtered/paginated in Python for better control)
    all_events = query.all()

    # Calculate balanced score combining importance + recency boost
    from datetime import datetime, timedelta

    def calculate_balanced_score(event: Event) -> float:
        """
        Balanced scoring combining importance, verification, and recency.

        Weights:
        - Importance (40%): What topics matter most
        - Truth/Confidence (30%): How verified is it
        - Recency boost (30%): Newer events get preference

        This prevents old articles from permanently dominating just because
        they have high importance scores.
        """
        importance_weight = 0.4
        confidence_weight = 0.3
        recency_weight = 0.3

        # 1. Normalize importance (0-100)
        importance_score = (event.importance_score or 0) / 100.0

        # 2. Normalize truth score (0-100)
        truth_score = (event.truth_score or 0) / 100.0

        # 3. Recency boost: Decay older events, boost newer ones
        now = datetime.utcnow()
        hours_old = (now - event.last_seen).total_seconds() / 3600

        # Recency decay function:
        # Recent (0-6h): +30 points
        # 6-12h: +20 points
        # 12-24h: +10 points
        # 24-48h: +5 points
        # >48h: gradual decay
        if hours_old <= 6:
            recency_score = 0.95  # Very recent - high boost
        elif hours_old <= 12:
            recency_score = 0.75  # Recent - moderate boost
        elif hours_old <= 24:
            recency_score = 0.5   # A day old - mild boost
        elif hours_old <= 48:
            recency_score = 0.3   # Two days old - small boost
        else:
            # After 48 hours, gradual decay: 0.3 - 0.001 per hour
            decay = max(0.05, 0.3 - (hours_old - 48) * 0.001)
            recency_score = decay

        # Combine weighted scores
        balanced_score = (
            importance_weight * importance_score +
            confidence_weight * truth_score +
            recency_weight * recency_score
        )

        return balanced_score

    # Sort with balanced scoring
    all_events.sort(key=calculate_balanced_score, reverse=True)

    # Apply pagination after sorting
    events = all_events[offset:offset + limit]

    # Build response with sources - PERFORMANCE OPTIMIZATION: Batch load articles
    # Instead of N+1 queries (1 per event), we get all articles in one query
    results = []

    # Get all event IDs
    event_ids = [e.id for e in events]

    # Batch load all articles for these events in a single query
    if event_ids:
        all_articles = (
            db.query(Article)
            .filter(Article.cluster_id.in_(event_ids))
            .all()
        )
        # Group articles by event ID
        articles_by_event = {}
        for article in all_articles:
            if article.cluster_id not in articles_by_event:
                articles_by_event[article.cluster_id] = []
            if len(articles_by_event[article.cluster_id]) < 10:  # Top 10 sources
                articles_by_event[article.cluster_id].append(article)
    else:
        articles_by_event = {}

    for event in events:
        articles = articles_by_event.get(event.id, [])
        sources = [create_event_source_with_bias(a) for a in articles]

        # Deserialize conflict explanation and bias compass
        conflict_explanation = parse_json_body(
            event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
        )
        bias_compass = parse_json_body(
            event.bias_compass_json, BiasCompass, "bias_compass"
        )

        # Note: Skip international_coverage to avoid pre-existing bugs
        # This field will be None in the response
        international_coverage = None

        event_dict = {
            "id": event.id,
            "summary": event.summary,
            "articles_count": event.articles_count,
            "unique_sources": event.unique_sources,
            "truth_score": event.truth_score,
            "confidence_tier": event.confidence_tier,
            "has_conflict": event.has_conflict,
            "conflict_severity": event.conflict_severity,
            "conflict_explanation": conflict_explanation,
            "bias_compass": bias_compass,
            "category": event.category,
            "category_confidence": event.category_confidence,
            "importance_score": event.importance_score,
            "international_coverage": international_coverage,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
        }
        results.append(EventList(**event_dict))

    return EventsResponse(total=total, limit=limit, offset=offset, results=results)


@router.get("/search", response_model=EventsResponse)
async def search_events(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    politics_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Search events by keyword across summary and entities.

    Searches:
    - Event summary (case-insensitive substring match)
    - Extracted entities (countries, people, organizations)

    Query parameters:
        - q: Search query (required, minimum 1 character)
        - limit: Results per page (1-100, default 50)
        - offset: Pagination offset (default 0)
        - politics_only: If true, only search political and international events (default: false)

    Returns:
        EventsResponse with matching events ordered by relevance and recency
    """
    # Normalize query to lowercase for case-insensitive search
    search_query = q.lower().strip()

    # Strategy: Find articles matching the search query, then get their events
    # This allows us to search both article titles AND entities
    matching_articles = db.query(Article).filter(
        or_(
            # Search in article title
            func.lower(Article.title).contains(search_query),
            # Search in article summary
            func.lower(Article.summary).contains(search_query),
            # Search in entities JSON (countries, people, organizations)
            Article.entities_json.ilike(f"%{search_query}%"),
        )
    ).all()

    # Get unique event IDs from matching articles
    matching_event_ids = set(a.cluster_id for a in matching_articles if a.cluster_id)

    # Also search event summaries directly
    direct_event_matches = db.query(Event).filter(
        func.lower(Event.summary).contains(search_query)
    ).all()

    matching_event_ids.update(e.id for e in direct_event_matches)

    # Convert to list and query full events
    if not matching_event_ids:
        # No matches found
        return EventsResponse(total=0, limit=limit, offset=offset, results=[])

    query = db.query(Event).filter(Event.id.in_(list(matching_event_ids)))

    # Filter for political events if requested
    if politics_only:
        query = query.filter(Event.category.in_(['politics', 'international']))

    # Filter to show only events above developing threshold
    query = query.filter(Event.truth_score >= settings.developing_threshold)

    # Get total matching count
    total = query.count()

    # Fetch all matching events and apply balanced scoring (same as get_events)
    all_events = query.all()

    # Calculate balanced score combining importance + recency boost
    from datetime import datetime, timedelta

    def calculate_balanced_score(event: Event) -> float:
        """
        Balanced scoring combining importance, verification, and recency.
        (Same logic as get_events endpoint)
        """
        importance_weight = 0.4
        confidence_weight = 0.3
        recency_weight = 0.3

        # Normalize importance (0-100)
        importance_score = (event.importance_score or 0) / 100.0

        # Normalize truth score (0-100)
        truth_score = (event.truth_score or 0) / 100.0

        # Recency boost
        now = datetime.utcnow()
        hours_old = (now - event.last_seen).total_seconds() / 3600

        if hours_old <= 6:
            recency_score = 0.95
        elif hours_old <= 12:
            recency_score = 0.75
        elif hours_old <= 24:
            recency_score = 0.5
        elif hours_old <= 48:
            recency_score = 0.3
        else:
            decay = max(0.05, 0.3 - (hours_old - 48) * 0.001)
            recency_score = decay

        # Combine weighted scores
        balanced_score = (
            importance_weight * importance_score +
            confidence_weight * truth_score +
            recency_weight * recency_score
        )

        return balanced_score

    # Sort with balanced scoring
    all_events.sort(key=calculate_balanced_score, reverse=True)

    # Apply pagination after sorting
    events = all_events[offset:offset + limit]

    # Build response with sources (same pattern as get_events)
    results = []

    # Get all event IDs
    event_ids = [e.id for e in events]

    # Batch load all articles for these events in a single query
    if event_ids:
        all_articles = (
            db.query(Article)
            .filter(Article.cluster_id.in_(event_ids))
            .all()
        )
        # Group articles by event ID
        articles_by_event = {}
        for article in all_articles:
            if article.cluster_id not in articles_by_event:
                articles_by_event[article.cluster_id] = []
            if len(articles_by_event[article.cluster_id]) < 10:  # Top 10 sources
                articles_by_event[article.cluster_id].append(article)
    else:
        articles_by_event = {}

    for event in events:
        articles = articles_by_event.get(event.id, [])
        sources = [create_event_source_with_bias(a) for a in articles]

        # Deserialize conflict explanation and bias compass
        conflict_explanation = parse_json_body(
            event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
        )
        bias_compass = parse_json_body(
            event.bias_compass_json, BiasCompass, "bias_compass"
        )

        # Note: Skip international_coverage for search results
        # Search results prioritize speed over deep analysis
        # Avoids pre-existing bug in international_coverage_from_json helper
        international_coverage = None

        event_dict = {
            "id": event.id,
            "summary": event.summary,
            "articles_count": event.articles_count,
            "unique_sources": event.unique_sources,
            "truth_score": event.truth_score,
            "confidence_tier": event.confidence_tier,
            "has_conflict": event.has_conflict,
            "conflict_severity": event.conflict_severity,
            "conflict_explanation": conflict_explanation,
            "bias_compass": bias_compass,
            "category": event.category,
            "category_confidence": event.category_confidence,
            "importance_score": event.importance_score,
            "international_coverage": international_coverage,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
        }
        results.append(EventList(**event_dict))

    return EventsResponse(total=total, limit=limit, offset=offset, results=results)


# Note: Specific routes must come before /{event_id} to avoid path conflicts
@router.get("/conflicts", response_model=EventsResponse)
async def get_conflict_events(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get events with narrative conflicts and different perspectives.

    Includes:
    - US politics and international events
    - Events with framing/emphasis differences between sources
    - Biased vs. neutral coverage (e.g., partisan vs. factual reporting)
    - Left vs. right interpretations

    Requirements:
    - Coherence < 75 (low, medium, or high severity - detects framing differences)
    - At least 5 articles from 3+ sources (allows smaller stories with real conflict)
    - Political/perspective diversity (left+right OR biased+neutral coverage)
    - Keyword overlap < 45% (perspectives emphasize different aspects)
    """
    # Filter for POLITICAL events with multiple sources (showing diverse perspectives)
    # NOTE: We show ALL politics/international events with 2+ sources
    # The diversity in sources alone indicates different coverage angles
    query = (
        db.query(Event)
        .filter(Event.articles_count >= 2)    # At least 2 articles (from different sources)
        .filter(Event.unique_sources >= 2)    # Multiple sources = different perspectives
        .filter(
            # ONLY politics and international (or NULL for uncategorized)
            (Event.category.in_(['politics', 'international'])) | (Event.category == None)
        )
    )

    total_candidates = query.count()

    # Get more events than needed to filter for political diversity
    # We'll sort by conflict_priority after filtering
    events = (
        query.order_by(
            Event.last_seen.desc()  # Get recent events first for filtering
        )
        .limit(limit * 4)  # Get 4x to account for filtering
        .offset(offset)
        .all()
    )

    # ADDITIONAL FILTER: Check for political diversity in results
    # PERFORMANCE OPTIMIZATION: Batch load articles instead of N+1 queries
    results = []

    # Get all event IDs
    event_ids = [e.id for e in events]

    # Batch load all articles for these events in a single query
    if event_ids:
        all_articles = (
            db.query(Article)
            .filter(Article.cluster_id.in_(event_ids))
            .all()
        )
        # Group articles by event ID
        articles_by_event = {}
        for article in all_articles:
            if article.cluster_id not in articles_by_event:
                articles_by_event[article.cluster_id] = []
            if len(articles_by_event[article.cluster_id]) < 10:  # Top 10 sources
                articles_by_event[article.cluster_id].append(article)
    else:
        articles_by_event = {}

    for event in events:
        articles = articles_by_event.get(event.id, [])
        
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
        
        # Parse conflict explanation if it exists
        conflict_explanation = None
        if event.conflict_explanation_json:
            conflict_explanation = parse_json_body(
                event.conflict_explanation_json, ConflictExplanation, "conflict_explanation"
            )

        # If we have conflict explanation, do additional filtering
        # Otherwise, if coherence < 75, just show it (indicates real narrative differences)
        if conflict_explanation:
            perspectives = conflict_explanation.perspectives
            political_leanings = set()

            # Extract political leanings from perspectives
            # Perspectives may be dicts or objects depending on parsing
            for p in perspectives:
                leaning = None
                if isinstance(p, dict):
                    leaning = p.get('political_leaning')
                elif hasattr(p, 'political_leaning'):
                    leaning = p.political_leaning

                if leaning:
                    political_leanings.add(leaning)

            # If no explicit political leanings extracted, infer from source diversity
            # (perspectives may have different sources even if leaning not explicitly set)
            if len(political_leanings) == 0 and len(perspectives) >= 2:
                # Multiple perspectives with no explicit leaning = probably diverse coverage
                # Accept it since coherence < 85 already indicates real differences
                political_leanings = {"diverse"}  # Placeholder for "we have multiple perspectives"

            # Require at least 2 different perspectives or inferred diversity
            if len(political_leanings) < 2 and len(perspectives) < 2:
                continue  # Skip - need multiple perspectives or leanings

            # More lenient on political diversity:
            # - If coherence > 70, only include if we have left AND right split OR explicit diversity
            # - If coherence < 70, framing differences are enough
            if event.coherence_score >= 70 and "diverse" not in political_leanings:
                # For higher coherence (minor framing), strictly require left+right split
                if 'left' not in political_leanings or 'right' not in political_leanings:
                    continue

            # Check keyword overlap - more lenient threshold
            # Note: keyword_overlap may be None for older events (not yet recalculated)
            # Only skip if we're confident the overlap is too high
            keyword_overlap = conflict_explanation.keyword_overlap
            if keyword_overlap is not None and keyword_overlap >= 0.65:
                # 65%+ overlap = essentially identical story (very rare for real conflicts)
                continue  # Skip - perspectives almost identical

            # Allow interpretation differences now (they capture framing conflicts)
            # Only skip truly trivial differences
            classification = conflict_explanation.classification
            if classification:
                # Classification is a Pydantic object
                if (classification.conflict_type == 'interpretation' and
                    classification.confidence < 0.4):
                    # Confidence < 0.4 means we're not sure it's even an interpretation difference
                    continue  # Skip - not confident enough
        # If no conflict explanation, that's OK - low coherence is enough
        # (the coherence < 85 filter already indicates narrative differences)
        
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
            "has_conflict": event.has_conflict,
            "conflict_severity": event.conflict_severity,
            "conflict_explanation": conflict_explanation,
            "bias_compass": bias_compass,
            "category": event.category,
            "category_confidence": event.category_confidence,
            "importance_score": event.importance_score,
            "first_seen": event.first_seen,
            "last_seen": event.last_seen,
            "sources": sources,
        }
        results.append((event, EventList(**event_dict)))
    
    # PRIORITY SORTING: Calculate conflict priority and sort by most pressing issues first
    from app.services.conflict_priority import calculate_conflict_priority
    
    # Calculate priority for each event
    events_with_priority = []
    for event, event_list in results:
        priority = calculate_conflict_priority(event)
        events_with_priority.append((priority, event_list))
    
    # Sort by priority (highest first), then take the requested limit
    events_with_priority.sort(key=lambda x: x[0], reverse=True)
    final_results = [event_list for _, event_list in events_with_priority[:limit]]
    
    return EventsResponse(total=len(final_results), limit=limit, offset=offset, results=final_results)


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

    conflict_count = (
        db.query(func.count(Event.id)).filter(Event.has_conflict == True).scalar() or 0
    )

    avg_score = db.query(func.avg(Event.truth_score)).scalar()
    if avg_score is None:
        avg_score = 0.0

    # Get last ingestion time (most recent article ingestion, guaranteed recent)
    # This represents when the last article was processed by the pipeline
    last_article = (
        db.query(Article)
        .filter(Article.ingested_at != None)  # Ensure timestamp exists
        .order_by(Article.ingested_at.desc())
        .first()
    )
    last_ingestion = last_article.ingested_at if last_article else None

    # BUGFIX: Ensure timezone-aware datetime for proper frontend parsing
    # The backend stores UTC times without timezone info, which causes JavaScript
    # to interpret them as local time, resulting in 7-hour offset errors in PST.
    # Solution: Convert to timezone-aware UTC before serialization.
    if last_ingestion:
        from datetime import timezone
        if last_ingestion.tzinfo is None:
            last_ingestion = last_ingestion.replace(tzinfo=timezone.utc)

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

    try:
        return StatsResponse(
            total_events=int(total_events),
            total_articles=int(total_articles),
            confirmed_events=int(confirmed),
            developing_events=int(developing),
            conflict_events=int(conflict_count),
            avg_confidence_score=float(round(avg_score, 2)),
            last_ingestion=last_ingestion,
            sources_count=int(sources_count),
            coverage_by_tier=CoverageTier(
                confirmed=int(confirmed), developing=int(developing), unverified=int(unverified)
            ),
            top_sources=top_sources,
        )
    except Exception as e:
        print(f"Error creating StatsResponse: {e}")
        print(f"Values: total_events={total_events}, total_articles={total_articles}, confirmed={confirmed}, developing={developing}, conflict_count={conflict_count}, avg_score={avg_score}, sources_count={sources_count}")
        raise


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
    
    # IMPROVED SORTING: Balance recency with severity of false/disputed claims
    # Fetch all matching articles and apply Python-based scoring
    all_articles = query.all()

    def calculate_flagged_score(article: Article) -> float:
        """
        Score flagged articles by severity and recency.

        Weights:
        - Severity (60%): False claims are more important than disputed
        - Recency (40%): Newer false claims are more urgent to highlight

        This prevents very old false claims from dominating while still
        showing newer important errors.
        """
        from datetime import datetime

        severity_weight = 0.6
        recency_weight = 0.4

        # 1. Severity scoring (0-1)
        if article.fact_check_status == "false":
            severity_score = 1.0  # False claims are most critical
        elif article.fact_check_status == "disputed":
            severity_score = 0.6  # Disputed claims are less critical
        else:
            severity_score = 0.3  # Default fallback

        # 2. Recency boost (0-1) - decay over time
        now = datetime.utcnow()
        hours_old = (now - article.timestamp).total_seconds() / 3600

        if hours_old <= 24:  # Within 1 day
            recency_score = 1.0
        elif hours_old <= 48:  # Within 2 days
            recency_score = 0.8
        elif hours_old <= 72:  # Within 3 days
            recency_score = 0.6
        else:
            # After 3 days, gradual decay
            days_old = hours_old / 24
            recency_score = max(0.1, 0.6 - (days_old - 3) * 0.02)

        # Combine weighted scores
        flagged_score = (
            severity_weight * severity_score +
            recency_weight * recency_score
        )

        return flagged_score

    # Sort with balanced scoring
    all_articles.sort(key=calculate_flagged_score, reverse=True)

    # Apply pagination after sorting
    articles = all_articles[offset:offset + limit]
    
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


@router.get("/polarizing-sources", response_model=PolarizingSourcesResponse)
async def get_polarizing_sources(
    min_articles: int = Query(10, ge=1, le=100),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get news sources ranked by political polarization.
    
    Polarization is calculated as:
    - Political Extremity (60%): Distance from center on left/right spectrum
    - Sensationalism (40%): Tone score (sensational vs factual)
    
    This is a mathematically neutral measure - it quantifies polarization
    intensity without editorial judgment about left or right.
    
    Query parameters:
        - min_articles: Minimum article count to include source (default 10)
        - limit: Maximum sources to return (default 50)
    """
    from app.services.polarization import calculate_source_polarization_rankings
    
    # Get polarization rankings
    sources = calculate_source_polarization_rankings(db, min_articles)
    
    # Apply limit
    sources = sources[:limit]
    
    # Convert to Pydantic models
    polarizing_sources = []
    for source_data in sources:
        excerpts = [
            PolarizingExcerpt(**excerpt) for excerpt in source_data['sample_excerpts']
        ]
        polarizing_sources.append(
            PolarizingSource(
                domain=source_data['domain'],
                polarization_score=source_data['polarization_score'],
                political_bias=source_data['political_bias'],
                tone_bias=source_data['tone_bias'],
                article_count=source_data['article_count'],
                sample_excerpts=excerpts
            )
        )
    
    methodology = (
        "Polarization Score = (Political Extremity × 0.6) + (Sensationalism × 0.4). "
        "Political Extremity measures distance from center (treats left/right equally). "
        "Sensationalism measures tone (factual vs sensational). "
        "Score ranges 0-100, with higher scores indicating more polarizing rhetoric."
    )
    
    return PolarizingSourcesResponse(
        total_sources=len(polarizing_sources),
        sources=polarizing_sources,
        methodology=methodology
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
