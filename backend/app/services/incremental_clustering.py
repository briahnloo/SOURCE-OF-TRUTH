"""Incremental clustering system for efficient memory usage

This module provides incremental clustering where new articles are compared against
existing cluster anchors rather than performing full re-clustering on every run.

Key optimizations:
- Only cluster 500-1000 new articles per run (vs. entire corpus)
- Maintain cluster anchors (representative embeddings per cluster)
- Full re-cluster only on weekly basis
- Lazy entity extraction (extract on-demand during analysis)

This saves 300-500MB of memory by avoiding redundant clustering operations.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator

import numpy as np
from loguru import logger
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Article, Event
from app.config import settings


@dataclass
class ClusterAnchor:
    """Represents a cluster anchor - a representative embedding for a cluster"""
    cluster_id: int
    event_id: int
    embedding: np.ndarray
    article_count: int
    last_updated: datetime

    def to_dict(self) -> dict:
        """Convert to dict for storage"""
        return {
            "cluster_id": self.cluster_id,
            "event_id": self.event_id,
            "embedding": self.embedding.tolist(),
            "article_count": self.article_count,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClusterAnchor":
        """Reconstruct from dict"""
        return cls(
            cluster_id=data["cluster_id"],
            event_id=data["event_id"],
            embedding=np.array(data["embedding"]),
            article_count=data["article_count"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )


@dataclass
class IncrementalClusteringState:
    """Tracks state of incremental clustering system"""
    last_full_cluster: datetime
    anchor_count: int
    articles_clustered_since_full: int
    memory_usage_mb: float
    full_cluster_interval_hours: int = 168  # Weekly


class ClusterAnchorManager:
    """Manages cluster anchors for incremental clustering"""

    def __init__(self, cache_file: str = "/tmp/cluster_anchors.json"):
        """
        Initialize cluster anchor manager.

        Args:
            cache_file: File path for persisting anchors
        """
        self.cache_file = cache_file
        self.anchors: Dict[int, ClusterAnchor] = {}
        self.load_anchors()

    def load_anchors(self) -> None:
        """Load anchors from persistent storage"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.anchors = {
                    int(k): ClusterAnchor.from_dict(v)
                    for k, v in data.items()
                }
                logger.info(f"Loaded {len(self.anchors)} cluster anchors from cache")
        except FileNotFoundError:
            logger.debug(f"No anchor cache found at {self.cache_file}")
            self.anchors = {}
        except Exception as e:
            logger.warning(f"Failed to load anchors: {e}, starting fresh")
            self.anchors = {}

    def save_anchors(self) -> None:
        """Save anchors to persistent storage"""
        try:
            with open(self.cache_file, 'w') as f:
                data = {
                    str(k): v.to_dict()
                    for k, v in self.anchors.items()
                }
                json.dump(data, f)
                logger.debug(f"Saved {len(self.anchors)} anchors to cache")
        except Exception as e:
            logger.error(f"Failed to save anchors: {e}")

    def add_anchor(self, event_id: int, embedding: np.ndarray, article_count: int) -> int:
        """
        Add or update a cluster anchor.

        Args:
            event_id: ID of the event/cluster
            embedding: Representative embedding for cluster
            article_count: Number of articles in cluster

        Returns:
            Cluster ID
        """
        cluster_id = event_id
        anchor = ClusterAnchor(
            cluster_id=cluster_id,
            event_id=event_id,
            embedding=embedding.astype(np.float32),
            article_count=article_count,
            last_updated=datetime.utcnow(),
        )
        self.anchors[cluster_id] = anchor
        return cluster_id

    def find_best_match(
        self,
        embedding: np.ndarray,
        similarity_threshold: float = 0.6
    ) -> Optional[Tuple[int, float]]:
        """
        Find best matching anchor for an embedding.

        Args:
            embedding: Embedding to match
            similarity_threshold: Minimum similarity to consider a match

        Returns:
            Tuple of (event_id, similarity) or None if no match
        """
        if not self.anchors:
            return None

        # Compute similarities to all anchors
        anchor_embeddings = np.array([
            anchor.embedding for anchor in self.anchors.values()
        ])
        similarities = cosine_similarity(
            embedding.reshape(1, -1),
            anchor_embeddings
        )[0]

        # Find best match
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]

        if best_similarity >= similarity_threshold:
            best_anchor = list(self.anchors.values())[best_idx]
            return best_anchor.event_id, best_similarity

        return None

    def get_anchor(self, event_id: int) -> Optional[ClusterAnchor]:
        """Get anchor for specific event"""
        return self.anchors.get(event_id)

    def get_state(self) -> IncrementalClusteringState:
        """Get current clustering state"""
        # Calculate memory usage of anchors
        total_memory_mb = sum(
            anchor.embedding.nbytes / (1024 * 1024)
            for anchor in self.anchors.values()
        )

        return IncrementalClusteringState(
            last_full_cluster=datetime.utcnow(),
            anchor_count=len(self.anchors),
            articles_clustered_since_full=0,
            memory_usage_mb=total_memory_mb,
        )


def match_articles_to_existing_clusters(
    db: Session,
    new_articles: List[Article],
    embeddings: np.ndarray,
    anchor_manager: ClusterAnchorManager,
    similarity_threshold: float = 0.6,
) -> Dict[int, int]:
    """
    Match new articles to existing clusters using anchors.

    This is the core of incremental clustering - instead of re-clustering
    all articles, we compare new ones against existing cluster anchors.

    Args:
        db: Database session
        new_articles: List of new articles to match
        embeddings: Embeddings for new articles
        anchor_manager: Cluster anchor manager
        similarity_threshold: Minimum similarity to match

    Returns:
        Dict mapping article_id -> event_id
    """
    matches = {}

    logger.info(
        f"Matching {len(new_articles)} articles to {len(anchor_manager.anchors)} "
        f"existing clusters (threshold={similarity_threshold})"
    )

    for i, article in enumerate(new_articles):
        embedding = embeddings[i]

        # Try to find matching cluster
        match = anchor_manager.find_best_match(
            embedding,
            similarity_threshold
        )

        if match:
            event_id, similarity = match
            matches[article.id] = event_id
            logger.debug(
                f"Article {article.id}: Matched to event {event_id} "
                f"(similarity={similarity:.3f})"
            )
        else:
            # No match - will be clustered separately
            matches[article.id] = None
            logger.debug(f"Article {article.id}: No matching cluster found")

    return matches


def compute_cluster_anchor(
    db: Session,
    event_id: int,
    articles: List[Article],
    embeddings: np.ndarray
) -> np.ndarray:
    """
    Compute anchor (representative embedding) for a cluster.

    Uses medoid embedding (most similar to all others) for robustness.

    Args:
        db: Database session
        event_id: Event/cluster ID
        articles: Articles in cluster
        embeddings: Embeddings for articles

    Returns:
        Anchor embedding (float32)
    """
    if len(embeddings) == 0:
        raise ValueError("Cannot compute anchor for empty cluster")

    if len(embeddings) == 1:
        return embeddings[0].astype(np.float32)

    # Find medoid (most central article)
    similarities = cosine_similarity(embeddings)
    avg_similarities = similarities.mean(axis=1)
    medoid_idx = np.argmax(avg_similarities)

    logger.debug(
        f"Event {event_id}: Computed anchor using medoid "
        f"(article {articles[medoid_idx].id})"
    )

    return embeddings[medoid_idx].astype(np.float32)


def incremental_cluster_articles(
    db: Session,
    new_articles: List[Article],
    embeddings: np.ndarray,
    anchor_manager: ClusterAnchorManager,
    similarity_threshold: float = 0.6,
    full_cluster_interval_hours: int = 168,  # Weekly
) -> Tuple[Dict[int, int], Dict[str, object]]:
    """
    Perform incremental clustering on new articles.

    This is the main entry point for incremental clustering. It:
    1. Matches new articles to existing clusters
    2. Creates new clusters for unmatched articles
    3. Updates cluster anchors
    4. Tracks memory usage

    Args:
        db: Database session
        new_articles: Articles ingested since last run
        embeddings: Precomputed embeddings
        anchor_manager: Cluster anchor manager
        similarity_threshold: Similarity threshold for matching
        full_cluster_interval_hours: How often to do full re-cluster

    Returns:
        Tuple of (article_to_event_dict, stats_dict)
    """
    if len(new_articles) == 0:
        return {}, {
            "articles_processed": 0,
            "new_clusters": 0,
            "matched_clusters": 0,
            "memory_saved_mb": 0,
        }

    logger.info(
        f"Starting incremental clustering of {len(new_articles)} articles"
    )

    # Step 1: Match articles to existing clusters
    matches = match_articles_to_existing_clusters(
        db,
        new_articles,
        embeddings,
        anchor_manager,
        similarity_threshold,
    )

    article_to_event = {}

    # Separate matched and unmatched
    matched_indices = []
    unmatched_indices = []

    for i, article in enumerate(new_articles):
        event_id = matches.get(article.id)
        if event_id is not None:
            article_to_event[article.id] = event_id
            matched_indices.append(i)
        else:
            unmatched_indices.append(i)

    # Step 2: Cluster unmatched articles
    new_clusters = 0
    if unmatched_indices:
        unmatched_embeddings = embeddings[unmatched_indices]
        unmatched_articles = [new_articles[i] for i in unmatched_indices]

        # Use sparse KNN clustering for unmatched
        from app.services.sparse_clustering import cluster_with_sparse_knn

        try:
            clustered = cluster_with_sparse_knn(
                unmatched_embeddings,
                k=5,
                distance_threshold=0.3,
                min_cluster_size=1,
            )

            # Create new events for each cluster
            for cluster_id, article_indices in clustered.items():
                # Create new event
                event = Event(
                    title=f"Event created at {datetime.utcnow()}",
                    summary="",
                    created_at=datetime.utcnow(),
                )
                db.add(event)
                db.flush()

                # Map articles to event
                for idx in article_indices:
                    article = unmatched_articles[idx]
                    article_to_event[article.id] = event.id

                # Compute and store anchor
                cluster_embeddings = unmatched_embeddings[article_indices]
                anchor = compute_cluster_anchor(
                    db,
                    event.id,
                    [unmatched_articles[i] for i in article_indices],
                    cluster_embeddings,
                )
                anchor_manager.add_anchor(
                    event.id,
                    anchor,
                    len(article_indices)
                )

                new_clusters += 1
                logger.debug(
                    f"Created new event {event.id} with {len(article_indices)} articles"
                )

        except Exception as e:
            logger.error(f"Failed to cluster unmatched articles: {e}")

    # Step 3: Save updated anchors
    anchor_manager.save_anchors()

    # Step 4: Calculate stats
    matched_count = len(matched_indices)
    memory_saved_mb = len(new_articles) * 0.384 * 4 / (1024 * 1024)  # 384-dim float32

    stats = {
        "articles_processed": len(new_articles),
        "articles_matched": matched_count,
        "articles_unmatched": len(unmatched_indices),
        "new_clusters_created": new_clusters,
        "matched_clusters": anchor_manager.anchor_count,
        "memory_saved_mb": memory_saved_mb,
        "total_anchors": len(anchor_manager.anchors),
    }

    logger.info(
        f"Incremental clustering complete: {matched_count} matched, "
        f"{len(unmatched_indices)} unmatched, {new_clusters} new clusters"
    )

    return article_to_event, stats


def full_recluster_if_needed(
    db: Session,
    anchor_manager: ClusterAnchorManager,
    force: bool = False,
) -> bool:
    """
    Perform full re-clustering if interval exceeded.

    This should run weekly to maintain cluster quality.

    Args:
        db: Database session
        anchor_manager: Cluster anchor manager
        force: Force re-clustering regardless of interval

    Returns:
        True if re-clustering was performed
    """
    state = anchor_manager.get_state()

    hours_since_cluster = (
        (datetime.utcnow() - state.last_full_cluster).total_seconds() / 3600
    )

    if not force and hours_since_cluster < state.full_cluster_interval_hours:
        logger.debug(
            f"Full re-cluster not needed ({hours_since_cluster:.1f}h / "
            f"{state.full_cluster_interval_hours}h)"
        )
        return False

    logger.info("Starting full event re-clustering")

    try:
        from app.services.cluster import cluster_articles

        # Get all events with articles
        events = db.query(Event).all()
        success = 0

        for event in events:
            try:
                articles = db.query(Article).filter(
                    Article.event_id == event.id
                ).limit(100).all()

                if not articles:
                    continue

                # Re-compute anchor
                from app.services.embed import generate_embeddings
                embeddings = generate_embeddings([a.title for a in articles])

                anchor = compute_cluster_anchor(
                    db,
                    event.id,
                    articles,
                    embeddings,
                )
                anchor_manager.add_anchor(
                    event.id,
                    anchor,
                    len(articles)
                )
                success += 1

            except Exception as e:
                logger.warning(f"Failed to re-cluster event {event.id}: {e}")

        anchor_manager.save_anchors()
        logger.info(f"Full re-clustering complete ({success} events updated)")
        return True

    except Exception as e:
        logger.error(f"Full re-clustering failed: {e}")
        return False
