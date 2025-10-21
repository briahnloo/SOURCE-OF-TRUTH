"""Underreported event detection"""

import json
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlparse

from app.config import settings
from app.models import Article, Event
from app.services.content_fetcher import ContentFetcher
from app.services.coherence import ArticleExcerpt
from openai import OpenAI
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


def extract_domain(source: str) -> str:
    """
    Extract clean domain from source URL or string.

    Args:
        source: Source URL or domain string

    Returns:
        Clean domain name
    """
    if source.startswith("http"):
        parsed = urlparse(source)
        domain = parsed.netloc
    else:
        domain = source

    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def add_excerpts_to_underreported_event(event: Event, articles: List[Article]) -> Event:
    """
    Extract single relevant excerpt from each article in an underreported event.
    
    Args:
        event: Underreported event
        articles: Articles in the event
        
    Returns:
        Updated event with excerpts in conflict_explanation_json
    """
    # For underreported, create a single perspective with excerpts
    content_fetcher = ContentFetcher(timeout=10)
    excerpts = []
    
    for article in articles[:5]:  # Process up to 5 articles
        try:
            article_text = content_fetcher.fetch_article_text(article.url)
            if not article_text:
                continue
            
            # Extract relevant excerpt using LLM
            excerpt = extract_underreported_excerpt(article, article_text, event.summary)
            if excerpt:
                excerpts.append(asdict(excerpt))
        except Exception as e:
            print(f"Failed to extract excerpt from {article.url}: {e}")
            continue
    
    # Store excerpts in a simple structure
    if excerpts:
        # Create a minimal perspective structure for underreported
        perspective = {
            "sources": [extract_domain(a.source) for a in articles],
            "article_count": len(articles),
            "representative_title": event.summary,
            "representative_excerpts": excerpts,
            "key_entities": [],
            "sentiment": "neutral",
            "focus_keywords": [],
        }
        
        # Store in conflict_explanation_json (reuse existing field)
        explanation = {
            "perspectives": [perspective],
            "key_difference": "Underreported by mainstream media",
            "difference_type": "coverage",
        }
        event.conflict_explanation_json = json.dumps(explanation)
    
    return event


def extract_underreported_excerpt(
    article: Article, 
    article_text: str, 
    event_summary: str
) -> Optional[ArticleExcerpt]:
    """
    Extract single most relevant excerpt from an underreported article.
    
    Uses LLM to find the passage that best summarizes why this story matters.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return None
    
    client = OpenAI(api_key=openai_key)
    
    truncated_text = " ".join(article_text.split()[:3000])
    
    prompt = f"""Extract the MOST relevant excerpt from this underreported news article.

Event Summary: {event_summary}
Article Title: {article.title}
Article Text: {truncated_text}

This story is covered by official sources (USGS, WHO, UN, etc.) or local outlets but has NOT been picked up by major wire services (AP, Reuters, AFP).

Task: Find the 2-4 sentence excerpt (150-250 words max) that BEST shows:
1. Why this story matters
2. Key facts and impact
3. What's actually happening on the ground

Prioritize excerpts with:
- Specific numbers, locations, or impacts
- Direct quotes from officials or witnesses  
- Information not widely reported elsewhere

Return ONLY valid JSON:
{{
  "excerpt": "exact quote with full context",
  "relevance_score": 0.95,
  "reason": "Brief explanation of why this excerpt matters"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert at identifying the most newsworthy excerpts from underreported stories. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=800,
    )
    
    response_text = response.choices[0].message.content.strip()
    
    # Parse JSON response
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    result = json.loads(response_text)
    
    return ArticleExcerpt(
        source=extract_domain(article.source),
        title=article.title,
        url=article.url,
        excerpt=result["excerpt"],
        relevance_score=result["relevance_score"],
    )
