"""RSS feed generation endpoint"""

from datetime import datetime, timedelta

from app.config import settings
from app.db import get_db
from app.models import Event
from fastapi import APIRouter, Depends, Response
from feedgen.feed import FeedGenerator
from sqlalchemy import and_
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/verified.xml")
async def get_verified_feed(db: Session = Depends(get_db)):
    """
    Generate RSS 2.0 feed of verified events.

    Includes:
        - Confirmed events (score >= 75)
        - Developing events (score >= 40)
        - Last 48 hours only
    """
    # Create feed generator
    fg = FeedGenerator()
    fg.id("http://localhost:3000/feeds/verified")
    fg.title("The Truthboard - Verified Events")
    fg.link(href="http://localhost:3000", rel="alternate")
    fg.link(href="http://localhost:8000/feeds/verified.xml", rel="self")
    fg.description("Truth-scored news events verified via open data sources")
    fg.language("en")

    # Get events from last 48 hours
    cutoff = datetime.utcnow() - timedelta(hours=48)
    events = (
        db.query(Event)
        .filter(
            and_(
                Event.truth_score >= settings.developing_threshold,
                Event.first_seen >= cutoff,
            )
        )
        .order_by(Event.truth_score.desc(), Event.first_seen.desc())
        .limit(50)  # Max 50 entries
        .all()
    )

    # Add feed entries
    for event in events:
        fe = fg.add_entry()
        fe.id(f"http://localhost:3000/events/{event.id}")
        fe.title(event.summary)
        fe.link(href=f"http://localhost:3000/events/{event.id}")

        # Build description
        description = (
            f"Event verified with confidence score {event.truth_score:.1f} "
            f"from {event.unique_sources} sources"
        )
        if event.evidence_flag:
            description += " including official/NGO sources"

        fe.description(description)
        fe.pubDate(event.first_seen)
        fe.category(term=event.confidence_tier.capitalize())

    # Generate RSS XML
    rss_str = fg.rss_str(pretty=True)

    return Response(content=rss_str, media_type="application/rss+xml")
