"""Truth confidence scoring"""

from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.models import Article, Event
from sqlalchemy.orm import Session

# Trusted news sources for political event verification
TRUSTED_NEWS_SOURCES = [
    'apnews.com', 'ap.org',
    'reuters.com',
    'bbc.com', 'bbc.co.uk', 'feeds.bbci.co.uk',
    'nytimes.com',
    'afp.com',
    'npr.org', 'feeds.npr.org',
    'pbs.org',
]


def calculate_source_score(unique_sources: int) -> float:
    """
    Calculate source diversity score (0-25 points).

    Diminishing returns after 5 sources.
    """
    normalized = min(unique_sources / 5.0, 1.0)
    return normalized * 25.0


def calculate_geo_score(geo_diversity: float) -> float:
    """
    Calculate geographic diversity score (0-40 points).

    Based on unique TLDs (target: 4+ countries).
    """
    return geo_diversity * 40.0


def calculate_evidence_score(evidence_flag: bool) -> float:
    """
    Calculate primary evidence score (0-20 points).

    Binary: 20 if official source present, else 0.
    """
    return 20.0 if evidence_flag else 0.0


def calculate_official_match_score(event: Event, db: Session) -> float:
    """
    Calculate official match score (0-15 points).

    Checks temporal proximity to official data feed events.
    Used for natural disasters and health events.
    """
    # Get official source articles in the event
    articles = db.query(Article).filter(Article.cluster_id == event.id).all()

    has_official = any(
        any(official in a.source.lower() for official in settings.official_sources)
        for a in articles
    )

    if not has_official:
        return 0.0

    # For MVP, if there's an official source in the cluster, give full points
    # In production, would check timestamp proximity to official feed
    return 15.0


def calculate_coherence_bonus(event: Event) -> float:
    """
    Bonus for narrative coherence (0-15 points).
    
    Replaces official_match for political events where sources
    agreeing strongly indicates truth.
    
    Args:
        event: Event to score
        
    Returns:
        Coherence bonus (0-15)
    """
    coherence = event.coherence_score or 0
    
    # Only give bonus for HIGH coherence (sources agree strongly)
    if coherence >= 90:
        return 15.0  # Perfect agreement
    elif coherence >= 80:
        return 10.0  # Strong agreement
    elif coherence >= 70:
        return 5.0   # Moderate agreement
    else:
        return 0.0  # Low coherence = conflicting narratives


def calculate_trusted_source_bonus(event: Event, db: Session) -> float:
    """
    Bonus for trusted primary news sources (0-15 points).
    
    Replaces evidence_score for political events.
    Wire services (AP, Reuters, AFP) and major broadcasters
    (BBC, NPR, PBS) serve as verification for political news.
    
    Args:
        event: Event to score
        db: Database session
        
    Returns:
        Trusted source bonus (0-15)
    """
    articles = db.query(Article).filter(Article.cluster_id == event.id).all()
    
    trusted_count = 0
    for article in articles:
        source_lower = article.source.lower()
        if any(trusted in source_lower for trusted in TRUSTED_NEWS_SOURCES):
            trusted_count += 1
    
    # Scaling: 1 = 5pts, 2 = 10pts, 3+ = 15pts
    if trusted_count >= 3:
        return 15.0
    elif trusted_count == 2:
        return 10.0
    elif trusted_count == 1:
        return 5.0
    else:
        return 0.0


def score_event(event: Event, db: Session) -> float:
    """
    Calculate truth confidence score with category-specific scoring.
    
    Natural disasters/health:
        - Use official sources (USGS, WHO, NASA)
        - Threshold: 75
    
    Political/international:
        - Use trusted news sources (AP, Reuters, BBC)
        - Use coherence bonus (sources agreeing)
        - Threshold: 60

    Args:
        event: Event to score
        db: Database session

    Returns:
        Truth score (0-100)
    """
    source_score = calculate_source_score(event.unique_sources)
    geo_score = calculate_geo_score(event.geo_diversity or 0.0)
    
    # Category-specific scoring
    if event.category in ['natural_disaster', 'health']:
        # Use official sources for scientific events
        evidence_score = calculate_evidence_score(event.evidence_flag)
        official_score = calculate_official_match_score(event, db)
    else:
        # Use trusted news sources for political events
        evidence_score = calculate_trusted_source_bonus(event, db)
        official_score = calculate_coherence_bonus(event)
    
    # Set official_match flag
    event.official_match = official_score > 0

    # Calculate total
    truth_score = source_score + geo_score + evidence_score + official_score

    return round(truth_score, 2)


def score_all_events(db: Session) -> int:
    """
    Score all events in the database.

    Args:
        db: Database session

    Returns:
        Number of events scored
    """
    events = db.query(Event).all()

    for event in events:
        event.truth_score = score_event(event, db)

    db.commit()

    print(f"✅ Scored {len(events)} events")

    return len(events)


def score_recent_events(db: Session, hours: int = 24) -> int:
    """
    Score events created in the last N hours.

    Args:
        db: Database session
        hours: Time window

    Returns:
        Number of events scored
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    events = db.query(Event).filter(Event.created_at >= cutoff).all()

    for event in events:
        event.truth_score = score_event(event, db)

    db.commit()

    print(f"✅ Scored {len(events)} recent events")

    return len(events)
