"""Truth confidence scoring"""

from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.models import Article, Event
from sqlalchemy.orm import Session


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


def score_event(event: Event, db: Session) -> float:
    """
    Calculate truth confidence score for an event.

    Formula:
        truth_score = (source_score * 0.25) +
                      (geo_score * 0.40) +
                      (evidence_score * 0.20) +
                      (official_score * 0.15)

    Args:
        event: Event to score
        db: Database session

    Returns:
        Truth score (0-100)
    """
    source_score = calculate_source_score(event.unique_sources)
    geo_score = calculate_geo_score(event.geo_diversity or 0.0)
    evidence_score = calculate_evidence_score(event.evidence_flag)
    official_score = calculate_official_match_score(event, db)

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
