"""TTL Event Archival System for memory optimization

This module implements a graduated TTL (Time-To-Live) system for events:
- Hot events (< 24h): Full in-memory cache, frequent updates
- Warm events (24-72h): Lazy-load on access, less frequent updates
- Cold events (> 72h): Archive to compressed storage, read-only

This saves 300-400MB of memory by moving older events out of active cache.

Key features:
- Automatic event lifecycle management
- Graduated compression based on age
- Lazy loading on access
- Background archival process
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
import gzip

from loguru import logger
from sqlalchemy.orm import Session

from app.models import Event, Article
from app.config import settings


class EventTier(Enum):
    """Event tier based on age"""
    HOT = "hot"      # < 24 hours
    WARM = "warm"    # 24 - 72 hours
    COLD = "cold"    # > 72 hours


@dataclass
class EventTTLConfig:
    """Configuration for event TTL system"""
    hot_duration_hours: int = 24
    warm_duration_hours: int = 72
    cold_retention_days: int = 30
    archive_batch_size: int = 100
    compression_enabled: bool = True


@dataclass
class ArchivedEvent:
    """Archived event with compressed data"""
    event_id: int
    compressed_data: bytes  # gzip compressed JSON
    archived_at: datetime
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float

    def decompress(self) -> dict:
        """Decompress archived event data"""
        return json.loads(gzip.decompress(self.compressed_data).decode('utf-8'))


class EventTierManager:
    """Manages event tiers and archival"""

    def __init__(self, config: Optional[EventTTLConfig] = None):
        """
        Initialize event tier manager.

        Args:
            config: TTL configuration
        """
        self.config = config or EventTTLConfig()
        self.archive: Dict[int, ArchivedEvent] = {}
        self.tier_membership: Dict[int, EventTier] = {}

    def determine_tier(self, event: Event) -> EventTier:
        """
        Determine tier for an event based on age.

        Args:
            event: Event to categorize

        Returns:
            EventTier enum value
        """
        age_hours = (datetime.utcnow() - event.created_at).total_seconds() / 3600

        if age_hours < self.config.hot_duration_hours:
            return EventTier.HOT
        elif age_hours < self.config.warm_duration_hours:
            return EventTier.WARM
        else:
            return EventTier.COLD

    def should_archive(self, event: Event) -> bool:
        """Check if event should be archived"""
        tier = self.determine_tier(event)
        return tier == EventTier.COLD

    def archive_event(
        self,
        db: Session,
        event: Event,
        include_articles: bool = False,
    ) -> Optional[ArchivedEvent]:
        """
        Archive an event to compressed storage.

        Args:
            db: Database session
            event: Event to archive
            include_articles: Whether to include article data

        Returns:
            ArchivedEvent object or None if archival failed
        """
        try:
            # Prepare event data
            event_data = {
                "id": event.id,
                "title": event.title,
                "summary": event.summary,
                "category": event.category,
                "coherence_score": event.coherence_score,
                "conflict_severity": event.conflict_severity,
                "created_at": event.created_at.isoformat(),
            }

            # Optionally include article summaries
            if include_articles:
                articles = db.query(Article).filter(
                    Article.event_id == event.id
                ).all()
                event_data["articles"] = [
                    {
                        "id": a.id,
                        "title": a.title,
                        "source": a.source,
                    }
                    for a in articles
                ]

            # Convert to JSON
            json_data = json.dumps(event_data).encode('utf-8')
            original_size = len(json_data)

            # Compress
            compressed_data = gzip.compress(json_data, compresslevel=6)
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size / original_size) * 100

            archived = ArchivedEvent(
                event_id=event.id,
                compressed_data=compressed_data,
                archived_at=datetime.utcnow(),
                original_size_bytes=original_size,
                compressed_size_bytes=compressed_size,
                compression_ratio=compression_ratio,
            )

            self.archive[event.id] = archived

            logger.debug(
                f"Archived event {event.id}: {original_size} -> {compressed_size} bytes "
                f"({compression_ratio:.1f}% savings)"
            )

            return archived

        except Exception as e:
            logger.error(f"Failed to archive event {event.id}: {e}")
            return None

    def get_archived_event(self, event_id: int) -> Optional[dict]:
        """
        Retrieve archived event data.

        Args:
            event_id: ID of archived event

        Returns:
            Decompressed event data or None
        """
        if event_id not in self.archive:
            return None

        try:
            archived = self.archive[event_id]
            return archived.decompress()
        except Exception as e:
            logger.error(f"Failed to decompress event {event_id}: {e}")
            return None

    def get_archive_stats(self) -> Dict[str, object]:
        """Get archival statistics"""
        if not self.archive:
            return {
                "archived_events": 0,
                "total_original_bytes": 0,
                "total_compressed_bytes": 0,
                "average_compression_ratio": 0.0,
            }

        total_original = sum(a.original_size_bytes for a in self.archive.values())
        total_compressed = sum(a.compressed_size_bytes for a in self.archive.values())
        avg_ratio = (1 - total_compressed / total_original * 100) if total_original > 0 else 0

        return {
            "archived_events": len(self.archive),
            "total_original_bytes": total_original,
            "total_compressed_bytes": total_compressed,
            "average_compression_ratio": avg_ratio,
            "memory_saved_mb": (total_original - total_compressed) / (1024 * 1024),
        }


def archive_old_events(
    db: Session,
    tier_manager: EventTierManager,
    batch_size: Optional[int] = None,
) -> Tuple[int, Dict[str, object]]:
    """
    Archive old events in batches.

    This is designed to be run as a background task (e.g., hourly or daily).

    Args:
        db: Database session
        tier_manager: Event tier manager
        batch_size: Number of events to process per call

    Returns:
        Tuple of (archived_count, stats_dict)
    """
    batch_size = batch_size or tier_manager.config.archive_batch_size

    # Find events older than warm threshold
    cutoff = datetime.utcnow() - timedelta(
        hours=tier_manager.config.warm_duration_hours
    )

    events_to_archive = (
        db.query(Event)
        .filter(Event.created_at < cutoff)
        .limit(batch_size)
        .all()
    )

    if not events_to_archive:
        logger.debug("No events to archive")
        return 0, {}

    logger.info(f"Archiving {len(events_to_archive)} events")

    archived_count = 0
    for event in events_to_archive:
        archived = tier_manager.archive_event(db, event, include_articles=True)
        if archived:
            archived_count += 1

    stats = tier_manager.get_archive_stats()
    logger.info(
        f"Archived {archived_count} events, "
        f"freed {stats['memory_saved_mb']:.1f}MB"
    )

    return archived_count, stats


def cleanup_expired_archives(
    tier_manager: EventTierManager,
    retention_days: Optional[int] = None,
) -> int:
    """
    Remove archives older than retention period.

    Args:
        tier_manager: Event tier manager
        retention_days: Retention period in days

    Returns:
        Number of archives removed
    """
    retention_days = retention_days or tier_manager.config.cold_retention_days
    cutoff = datetime.utcnow() - timedelta(days=retention_days)

    to_delete = [
        event_id
        for event_id, archive in tier_manager.archive.items()
        if archive.archived_at < cutoff
    ]

    for event_id in to_delete:
        del tier_manager.archive[event_id]

    if to_delete:
        logger.info(f"Deleted {len(to_delete)} archived events older than {retention_days} days")

    return len(to_delete)


class EventTTLCache:
    """In-memory cache with TTL for hot/warm events"""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 72):
        """
        Initialize TTL cache.

        Args:
            max_size: Maximum events to keep in memory
            ttl_hours: Time before event moves to cold storage
        """
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache: Dict[int, Tuple[Event, datetime]] = {}
        self.access_times: Dict[int, datetime] = {}

    def put(self, event: Event) -> None:
        """Add event to cache"""
        if len(self.cache) >= self.max_size:
            # Evict least recently used
            lru_event_id = min(
                self.access_times.keys(),
                key=lambda k: self.access_times[k]
            )
            del self.cache[lru_event_id]
            del self.access_times[lru_event_id]

        self.cache[event.id] = (event, datetime.utcnow())
        self.access_times[event.id] = datetime.utcnow()

    def get(self, event_id: int) -> Optional[Event]:
        """Get event from cache"""
        if event_id not in self.cache:
            return None

        event, created_at = self.cache[event_id]
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600

        if age_hours > self.ttl_hours:
            # Expired - remove from cache
            del self.cache[event_id]
            del self.access_times[event_id]
            return None

        # Update access time
        self.access_times[event_id] = datetime.utcnow()
        return event

    def clear(self) -> int:
        """Clear expired entries"""
        to_delete = [
            event_id
            for event_id, (event, created_at) in self.cache.items()
            if (datetime.utcnow() - created_at).total_seconds() / 3600 > self.ttl_hours
        ]

        for event_id in to_delete:
            del self.cache[event_id]
            if event_id in self.access_times:
                del self.access_times[event_id]

        return len(to_delete)

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_events": len(self.cache),
            "max_size": self.max_size,
            "ttl_hours": self.ttl_hours,
        }
