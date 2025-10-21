"""Article normalization and deduplication"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import spacy
from app.config import settings
from app.models import Article
from sqlalchemy.orm import Session

import spacy
from app.services.service_registry import get_nlp_model, get_fact_checker


def get_nlp():
    """Get the singleton spaCy NLP model instance"""
    return get_nlp_model()


def detect_language(text: str) -> str:
    """
    Simple language detection (English only for MVP).

    Returns:
        "en" or "unknown"
    """
    # For MVP, we assume English if it contains mostly ASCII characters
    if not text:
        return "unknown"

    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)

    return "en" if ascii_ratio > 0.8 else "unknown"


def extract_entities(text: str) -> List[str]:
    """
    Extract named entities from text using spaCy.

    Args:
        text: Input text

    Returns:
        List of entity strings
    """
    if not text:
        return []

    try:
        nlp = get_nlp()

        # Limit text length to avoid memory issues
        text = text[:1000]

        doc = nlp(text)

        # Extract unique entities
        entities = list(set([ent.text for ent in doc.ents]))

        return entities[:20]  # Limit to top 20
    except Exception as e:
        print(f"Entity extraction error: {e}")
        return []


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.

    Removes tracking parameters and normalizes format.
    """
    try:
        parsed = urlparse(url)
        # Remove common tracking params
        # For MVP, just use the URL as-is (unique constraint handles duplicates)
        return url.strip()
    except:
        return url


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles.

    Simple implementation using word overlap for MVP.
    """
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0


def is_duplicate(article: Dict[str, Any], db: Session) -> bool:
    """
    Check if article is a duplicate.

    Checks:
        1. Exact URL match
        2. High title similarity (>0.9) from same source
    """
    # Check URL
    existing = db.query(Article).filter(Article.url == article["url"]).first()
    if existing:
        return True

    # Check title similarity within same source
    source = article.get("source", "")
    title = article.get("title", "")

    if source and title:
        recent_articles = (
            db.query(Article)
            .filter(Article.source == source)
            .order_by(Article.ingested_at.desc())
            .limit(50)
            .all()
        )

        for existing_article in recent_articles:
            similarity = calculate_title_similarity(title, existing_article.title)
            if similarity > 0.9:
                return True

    return False


def normalize_and_store(articles: List[Dict[str, Any]], db: Session) -> tuple[int, int]:
    """
    Normalize articles and store in database.

    Args:
        articles: List of raw article dictionaries
        db: Database session

    Returns:
        Tuple of (stored_count, duplicate_count)
    """
    stored = 0
    duplicates = 0

    for article_data in articles:
        # Validate required fields
        if not article_data.get("title") or not article_data.get("url"):
            continue

        # Check for duplicates
        if is_duplicate(article_data, db):
            duplicates += 1
            continue

        # Detect language
        text = f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        language = detect_language(text)

        # Skip non-English for MVP
        if language != "en":
            continue

        # Extract entities
        entities = extract_entities(text)

        # Create article model
        article = Article(
            source=article_data.get("source", "unknown"),
            title=article_data["title"][:1000],  # Limit length
            url=normalize_url(article_data["url"]),
            timestamp=article_data.get("timestamp", datetime.utcnow()),
            language=language,
            summary=article_data.get("summary", "")[:1000],
            text_snippet=article_data.get("summary", "")[:500],
            entities_json=json.dumps(entities),
            cluster_id=None,  # Will be assigned later
        )

        # Run fact-checking
        fact_checker = get_fact_checker()
        if fact_checker:
            try:
                status, flags = fact_checker.check_article(
                    title=article.title,
                    summary=article.summary or "",
                    url=article.url,
                    source=article.source,
                )
                article.fact_check_status = status
                if flags:
                    article.fact_check_flags_json = json.dumps(
                        [asdict(f) for f in flags]
                    )
            except Exception as e:
                print(f"Fact-check error for {article.url}: {e}")
                # Continue without fact-check data

        try:
            db.add(article)
            db.commit()
            stored += 1
        except Exception as e:
            db.rollback()
            print(f"Error storing article: {e}")
            duplicates += 1

    return stored, duplicates
