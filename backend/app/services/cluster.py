"""Article clustering using DBSCAN"""

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
from app.config import settings
from app.models import Article, Event
from app.services.bias import BiasAnalyzer
from app.services.coherence import calculate_narrative_coherence
from app.services.embed import generate_embeddings
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from sqlalchemy.orm import Session


def categorize_event(articles: List[Article], summary: str) -> Tuple[str, float]:
    """
    Categorize an event based on article content and sources.
    
    Args:
        articles: List of articles in the event
        summary: Event summary text
    
    Returns:
        Tuple of (category, confidence) where category is one of:
        'politics', 'natural_disaster', 'health', 'crime', 'international', 'other'
        and confidence is 0.0-1.0
    """
    # Combine all text for analysis
    text_combined = summary.lower()
    for article in articles[:5]:  # Check first 5 articles
        text_combined += " " + article.title.lower()
        if article.summary:
            text_combined += " " + article.summary.lower()
    
    # Check sources for official classifications
    sources = [article.source.lower() for article in articles]
    
    # Natural disaster keywords and sources
    if any(source in 'usgs.gov' for source in sources):
        return ('natural_disaster', 0.95)
    
    natural_disaster_keywords = [
        'earthquake', 'magnitude', 'tsunami', 'volcano', 'eruption',
        'hurricane', 'typhoon', 'cyclone', 'tornado', 'flood', 'wildfire',
        'avalanche', 'landslide', 'drought'
    ]
    natural_disaster_score = sum(1 for kw in natural_disaster_keywords if kw in text_combined)
    
    # Health/pandemic keywords and sources
    if any(source in 'who.int' for source in sources):
        return ('health', 0.95)
    
    health_keywords = [
        'outbreak', 'epidemic', 'pandemic', 'disease', 'virus', 'vaccine',
        'covid', 'infection', 'who', 'cdc', 'health crisis'
    ]
    health_score = sum(1 for kw in health_keywords if kw in text_combined)
    
    # Politics keywords
    politics_keywords = [
        'trump', 'biden', 'president', 'congress', 'senate', 'house',
        'democrat', 'republican', 'election', 'vote', 'campaign', 'policy',
        'legislation', 'bill', 'law', 'government', 'administration',
        'white house', 'capitol', 'political', 'party', 'lawmakers',
        'prime minister', 'parliament', 'ceasefire', 'peace deal',
        'protest', 'rally', 'demonstration'
    ]
    politics_score = sum(1 for kw in politics_keywords if kw in text_combined)
    
    # International/conflict keywords
    international_keywords = [
        'israel', 'gaza', 'hamas', 'ukraine', 'russia', 'war', 'military',
        'strike', 'attack', 'conflict', 'troops', 'ceasefire', 'hostage',
        'nato', 'un security', 'diplomatic', 'sanctions', 'treaty'
    ]
    international_score = sum(1 for kw in international_keywords if kw in text_combined)
    
    # Crime keywords
    crime_keywords = [
        'murder', 'killed', 'shooting', 'robbery', 'theft', 'stolen',
        'arrested', 'police', 'investigation', 'suspect', 'heist',
        'criminal', 'prison', 'sentenced'
    ]
    crime_score = sum(1 for kw in crime_keywords if kw in text_combined)
    
    # Determine category based on scores
    scores = {
        'natural_disaster': natural_disaster_score,
        'health': health_score,
        'politics': politics_score,
        'international': international_score,
        'crime': crime_score
    }
    
    max_category = max(scores, key=scores.get)
    max_score = scores[max_category]
    
    # If no strong signal, classify as 'other'
    if max_score < 2:
        return ('other', 0.3)
    
    # Calculate confidence based on score strength
    # High score = high confidence, but cap at 0.9 for keyword-based classification
    confidence = min(0.3 + (max_score * 0.1), 0.9)
    
    return (max_category, confidence)


def cluster_articles(db: Session) -> int:
    """
    Cluster recent articles and create/update events.

    Uses DBSCAN on sentence embeddings within a rolling time window.

    Args:
        db: Database session

    Returns:
        Number of clusters (events) created
    """
    # Get unclustered articles from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=settings.clustering_window_hours)

    articles = (
        db.query(Article)
        .filter(Article.timestamp >= cutoff)
        .filter(Article.cluster_id == None)
        .order_by(Article.timestamp.desc())
        .all()
    )

    if len(articles) < settings.dbscan_min_samples:
        print(f"Not enough articles to cluster: {len(articles)}")
        return 0

    print(f"Clustering {len(articles)} articles...")

    # Generate embeddings
    texts = [f"{a.title} {a.summary or ''}" for a in articles]
    embeddings = generate_embeddings(texts)

    # Compute cosine distance matrix
    distances = cosine_distances(embeddings)

    # Apply DBSCAN
    clustering = DBSCAN(
        eps=settings.dbscan_eps,
        min_samples=settings.dbscan_min_samples,
        metric="precomputed",
    ).fit(distances)

    labels = clustering.labels_

    # Count clusters (excluding noise with label -1)
    unique_labels = set(labels)
    n_clusters = len([l for l in unique_labels if l != -1])

    print(f"Found {n_clusters} clusters (noise: {list(labels).count(-1)} articles)")

    # Create events for each cluster
    events_created = 0

    for label in unique_labels:
        if label == -1:  # Skip noise
            continue

        # Get articles in this cluster
        cluster_indices = np.where(labels == label)[0]
        cluster_articles = [articles[i] for i in cluster_indices]
        cluster_embeddings = embeddings[cluster_indices]

        # Create event summary (use most common title words or first article)
        event = create_event_from_cluster(cluster_articles, cluster_embeddings, db)

        if event:
            # Assign cluster_id to articles
            for article in cluster_articles:
                article.cluster_id = event.id

            db.commit()
            events_created += 1

    print(f"✅ Created {events_created} new events")

    return events_created


def create_event_from_cluster(
    articles: List[Article], embeddings: np.ndarray, db: Session
) -> Event:
    """
    Create an Event from a cluster of articles.

    Args:
        articles: List of articles in the cluster
        embeddings: Pre-computed embeddings for the articles
        db: Database session

    Returns:
        Created Event object
    """
    # Generate summary (use longest title as proxy)
    summary = max(articles, key=lambda a: len(a.title)).title

    # Collect metadata
    unique_sources = len(set(a.source for a in articles))
    first_seen = min(a.timestamp for a in articles)
    last_seen = max(a.timestamp for a in articles)

    # Calculate geographic diversity (count unique TLDs)
    tlds = set()
    for article in articles:
        try:
            import tldextract

            extracted = tldextract.extract(article.source)
            if extracted.suffix:
                tlds.add(extracted.suffix)
        except:
            pass

    geo_diversity = min(len(tlds) / 4.0, 1.0)  # Normalize to 0-1

    # Check for evidence flag (any official source)
    evidence_flag = any(
        any(official in article.source.lower() for official in settings.official_sources)
        for article in articles
    )

    # For now, set official_match to False (will be updated by scoring)
    official_match = False

    # Collect languages
    languages = list(set(a.language for a in articles if a.language))

    # Initial placeholder score (will be recalculated by scoring service)
    truth_score = 50.0

    # Calculate narrative coherence
    coherence_score, conflict_severity, explanation = calculate_narrative_coherence(
        articles, embeddings
    )
    has_conflict = conflict_severity != "none"

    # Serialize conflict explanation to JSON
    conflict_explanation_json = None
    if explanation:
        conflict_explanation_json = json.dumps(asdict(explanation))

    # Calculate bias compass
    bias_analyzer = BiasAnalyzer()
    article_sources = [a.source for a in articles]
    bias_score = bias_analyzer.calculate_event_bias(article_sources)
    bias_compass_json = json.dumps(asdict(bias_score))

    # Categorize event
    category, category_confidence = categorize_event(articles, summary)

    # Create event
    event = Event(
        summary=summary,
        articles_count=len(articles),
        unique_sources=unique_sources,
        geo_diversity=geo_diversity,
        evidence_flag=evidence_flag,
        official_match=official_match,
        truth_score=truth_score,
        underreported=False,  # Will be set by underreported service
        coherence_score=coherence_score,
        has_conflict=has_conflict,
        conflict_severity=conflict_severity,
        conflict_explanation_json=conflict_explanation_json,
        bias_compass_json=bias_compass_json,
        category=category,
        category_confidence=category_confidence,
        first_seen=first_seen,
        last_seen=last_seen,
        languages_json=str(languages),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event
