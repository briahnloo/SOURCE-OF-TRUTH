"""Article clustering using DBSCAN"""

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from app.config import settings
from app.models import Article, Event
from app.services.service_registry import get_bias_analyzer
from app.services.coherence import calculate_narrative_coherence
from app.services.embed import generate_embeddings
from loguru import logger
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances, cosine_similarity
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


def update_event_with_new_articles(event: Event, new_articles: List[Article], db: Session) -> Event:
    """
    Recalculate event metrics when new articles are added.
    
    Args:
        event: Existing event
        new_articles: Newly clustered articles
        db: Database session
        
    Returns:
        Updated event
    """
    # Get all articles (existing + new)
    all_articles = db.query(Article).filter(Article.cluster_id == event.id).all()
    
    # Regenerate embeddings for ALL articles
    texts = [f"{a.title} {a.summary or ''}" for a in all_articles]
    embeddings = generate_embeddings(texts)
    
    # Recalculate coherence (THIS IS KEY)
    coherence_score, conflict_severity, explanation = calculate_narrative_coherence(
        all_articles, embeddings
    )
    
    # Check if conflict status changed
    was_conflicted = event.has_conflict
    is_now_conflicted = conflict_severity != "none"
    
    if not was_conflicted and is_now_conflicted:
        # Conflict emerged - record when it happened
        event.conflict_detected_at = datetime.utcnow()
        logger.warning(f"Event {event.id} became conflicted! New articles introduced contradictions.")
        # Could send Discord alert here
    
    # Update event fields
    event.articles_count = len(all_articles)
    event.unique_sources = len(set(a.source for a in all_articles))
    event.last_seen = max(a.timestamp for a in all_articles)
    event.coherence_score = coherence_score
    event.has_conflict = is_now_conflicted
    event.conflict_severity = conflict_severity
    
    if explanation:
        event.conflict_explanation_json = json.dumps(asdict(explanation))
    
    # Recalculate bias compass
    bias_analyzer = get_bias_analyzer()
    article_sources = [a.source for a in all_articles]
    bias_score = bias_analyzer.calculate_event_bias(article_sources)
    event.bias_compass_json = json.dumps(asdict(bias_score))
    
    db.commit()
    db.refresh(event)
    
    return event


def try_match_to_event(article: Article, article_emb: np.ndarray, event: Event, db: Session) -> bool:
    """
    Try to match a new article to an existing event.
    
    Uses semantic similarity threshold.
    
    Args:
        article: New article to match
        article_emb: Pre-computed embedding for the article
        event: Existing event to try matching with
        db: Database session
        
    Returns:
        True if article matches this event
    """
    # Get event's existing articles (sample up to 5 for efficiency)
    event_articles = db.query(Article).filter(Article.cluster_id == event.id).limit(5).all()
    
    if not event_articles:
        return False
    
    # Calculate similarity with event's articles
    event_texts = [f"{a.title} {a.summary or ''}" for a in event_articles]
    event_embeddings = generate_embeddings(event_texts)
    
    # Use cosine similarity
    similarities = cosine_similarity([article_emb], event_embeddings)[0]
    
    # If ANY article in event is similar enough, it's a match
    # Use 0.7 threshold (1 - eps = 1 - 0.3)
    max_similarity = max(similarities)
    
    return max_similarity >= 0.7


def cluster_unmatched_articles(
    articles: List[Article], 
    db: Session, 
    precomputed_embeddings: Optional[np.ndarray] = None
) -> int:
    """
    Cluster articles that didn't match existing events.
    
    This is the original DBSCAN clustering logic.
    
    Args:
        articles: List of unmatched articles
        db: Database session
        precomputed_embeddings: Optional pre-computed embeddings to avoid regenerating
        
    Returns:
        Number of new events created
    """
    if len(articles) < settings.dbscan_min_samples:
        logger.debug(f"Not enough articles to cluster: {len(articles)}")
        return 0

    logger.info(f"Clustering {len(articles)} unmatched articles into new events...")

    # Use precomputed embeddings if available, otherwise generate
    if precomputed_embeddings is not None:
        embeddings = precomputed_embeddings
    else:
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

    logger.info(f"Found {n_clusters} new clusters (noise: {list(labels).count(-1)} articles)")

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

    logger.info(f"✅ Created {events_created} new events")

    return events_created


def cluster_articles(db: Session) -> int:
    """
    Cluster recent articles and create/update events.
    
    First tries to match new articles with existing events, then clusters
    remaining unmatched articles using DBSCAN.

    Args:
        db: Database session

    Returns:
        Number of clusters (events) created or updated
    """
    # Get unclustered articles from last 48 hours (EXTENDED from 24h)
    cutoff = datetime.utcnow() - timedelta(hours=48)
    
    new_articles = (
        db.query(Article)
        .filter(Article.timestamp >= cutoff)
        .filter(Article.cluster_id == None)
        .order_by(Article.timestamp.desc())
        .all()
    )
    
    if not new_articles:
        logger.debug("No new articles to cluster")
        return 0
    
    # Get ACTIVE events (last 72 hours) for potential matching
    event_cutoff = datetime.utcnow() - timedelta(hours=72)
    active_events = (
        db.query(Event)
        .filter(Event.last_seen >= event_cutoff)
        .all()
    )
    
    logger.info(f"Clustering {len(new_articles)} articles against {len(active_events)} active events...")
    
    # OPTIMIZATION: Generate all article embeddings at once (batch processing)
    article_texts = [f"{a.title} {a.summary or ''}" for a in new_articles]
    article_embeddings = generate_embeddings(article_texts)
    
    # OPTIMIZATION: Pre-compute event embeddings once (cache them)
    event_embedding_cache = {}
    for event in active_events:
        event_articles = db.query(Article).filter(Article.cluster_id == event.id).limit(5).all()
        if event_articles:
            event_texts = [f"{a.title} {a.summary or ''}" for a in event_articles]
            event_embedding_cache[event.id] = generate_embeddings(event_texts)
    
    logger.info(f"Pre-computed embeddings for {len(event_embedding_cache)} events")
    
    # For each new article, try to match with existing events first
    unmatched_articles = []
    unmatched_embeddings = []
    updated_events = set()
    
    for idx, article in enumerate(new_articles):
        matched = False
        article_embedding = article_embeddings[idx]
        
        # Try matching with each active event using cached embeddings
        for event in active_events:
            if event.id in event_embedding_cache:
                # Use cached embeddings
                event_embs = event_embedding_cache[event.id]
                similarities = cosine_similarity([article_embedding], event_embs)[0]
                max_similarity = max(similarities)
                
                if max_similarity >= 0.7:
                    article.cluster_id = event.id
                    updated_events.add(event.id)
                    matched = True
                    logger.debug(f"Article {article.id} matched to event {event.id} (sim={max_similarity:.3f})")
                    break
        
        if not matched:
            unmatched_articles.append(article)
            unmatched_embeddings.append(article_embedding)
    
    db.commit()
    
    logger.info(f"Matched {len(new_articles) - len(unmatched_articles)} articles to existing events")
    logger.info(f"Updating {len(updated_events)} events with new articles")
    
    # Update events that got new articles
    for event_id in updated_events:
        event = db.query(Event).filter(Event.id == event_id).first()
        new_event_articles = [a for a in new_articles if a.cluster_id == event_id]
        update_event_with_new_articles(event, new_event_articles, db)
    
    # Cluster remaining unmatched articles into NEW events
    if len(unmatched_articles) >= settings.dbscan_min_samples:
        # Pass pre-computed embeddings to avoid regenerating
        new_events_created = cluster_unmatched_articles(
            unmatched_articles, 
            db, 
            precomputed_embeddings=np.array(unmatched_embeddings)
        )
    else:
        logger.debug(f"Only {len(unmatched_articles)} unmatched articles, need {settings.dbscan_min_samples} minimum")
        new_events_created = 0
    
    total_processed = new_events_created + len(updated_events)
    logger.info(f"✅ Processed {total_processed} events ({new_events_created} new, {len(updated_events)} updated)")
    
    return total_processed


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
    bias_analyzer = get_bias_analyzer()
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
