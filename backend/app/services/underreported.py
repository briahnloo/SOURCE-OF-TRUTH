"""Underreported event detection"""

from datetime import datetime, timedelta

from app.config import settings
from app.models import Article, Event
from sqlalchemy.orm import Session


def detect_underreported(db: Session) -> int:
    """
    Detect and flag underreported events.

    Criteria:
        - Present in NGO/Gov feeds OR small/local sources
        - Absent from major wires (AP, Reuters, AFP)
        - Within 48-hour window
        - Has >= 2 sources

    Args:
        db: Database session

    Returns:
        Number of events flagged as underreported
    """
    # Get events from last 48 hours with sufficient coverage
    cutoff = datetime.utcnow() - timedelta(hours=settings.underreported_window_hours)

    events = (
        db.query(Event)
        .filter(Event.first_seen >= cutoff)
        .filter(Event.articles_count >= settings.underreported_min_sources)
        .all()
    )

    flagged = 0

    for event in events:
        # Get articles for this event
        articles = db.query(Article).filter(Article.cluster_id == event.id).all()

        # Check if has NGO/Gov source
        has_ngo_gov = any(
            any(official in article.source.lower() for official in settings.official_sources)
            for article in articles
        )

        # Check if has major wire coverage
        has_major_wire = any(
            any(wire in article.source.lower() for wire in settings.major_wires)
            for article in articles
        )

        # Flag as underreported if NGO/Gov present but no major wire coverage
        if has_ngo_gov and not has_major_wire:
            event.underreported = True
            flagged += 1
        elif not has_major_wire and event.articles_count >= 3:
            # Also flag if multiple sources but no major wire
            # (catches local/regional stories)
            event.underreported = True
            flagged += 1
        else:
            event.underreported = False

    db.commit()

    print(f"✅ Flagged {flagged} underreported events")

    return flagged
