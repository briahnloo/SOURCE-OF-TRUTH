"""Article clustering using DBSCAN"""

from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
from app.config import settings
from app.models import Article, Event
from app.services.embed import generate_embeddings
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from sqlalchemy.orm import Session


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

        # Create event summary (use most common title words or first article)
        event = create_event_from_cluster(cluster_articles, db)

        if event:
            # Assign cluster_id to articles
            for article in cluster_articles:
                article.cluster_id = event.id

            db.commit()
            events_created += 1

    print(f"✅ Created {events_created} new events")

    return events_created


def create_event_from_cluster(articles: List[Article], db: Session) -> Event:
    """
    Create an Event from a cluster of articles.

    Args:
        articles: List of articles in the cluster
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
        first_seen=first_seen,
        last_seen=last_seen,
        languages_json=str(languages),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event
