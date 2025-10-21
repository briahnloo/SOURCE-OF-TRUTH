"""Lightweight scheduler optimized for Render free tier"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests
from loguru import logger

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Article, Event
from app.services.cluster import cluster_articles
from app.services.normalize import normalize_and_store
from app.services.score import score_recent_events

# Import only lightweight fetchers
from app.services.fetch.rss import fetch_rss_articles
from app.services.fetch.newsapi import fetch_newsapi_articles


def run_lightweight_ingestion() -> Dict:
    """
    Lightweight ingestion pipeline optimized for Render free tier.
    
    Only fetches from 2 sources (RSS + NewsAPI) to stay within limits.
    """
    logger.info("🚀 Starting lightweight ingestion pipeline...")
    
    start_time = time.time()
    stats = {
        "articles_fetched": 0,
        "articles_stored": 0,
        "events_created": 0,
        "events_scored": 0,
        "errors": []
    }
    
    try:
        # Initialize database
        init_db()
        db = SessionLocal()
        
        # Step 1: Fetch from lightweight sources only
        logger.info("📡 Step 1: Fetching articles from lightweight sources...")
        
        all_articles = []
        
        # RSS feeds (lightweight)
        try:
            rss_articles = fetch_rss_articles(minutes=60)  # Last hour only
            all_articles.extend(rss_articles)
            logger.info(f"✅ RSS: {len(rss_articles)} articles")
        except Exception as e:
            logger.error(f"❌ RSS failed: {e}")
            stats["errors"].append(f"RSS: {str(e)}")
        
        # NewsAPI (if key available)
        if settings.newsapi_key:
            try:
                newsapi_articles = fetch_newsapi_articles(minutes=60)
                all_articles.extend(newsapi_articles)
                logger.info(f"✅ NewsAPI: {len(newsapi_articles)} articles")
            except Exception as e:
                logger.error(f"❌ NewsAPI failed: {e}")
                stats["errors"].append(f"NewsAPI: {str(e)}")
        
        stats["articles_fetched"] = len(all_articles)
        
        if not all_articles:
            logger.warning("⚠️ No articles fetched, skipping processing")
            return stats
        
        # Step 2: Normalize and store (lightweight)
        logger.info("📝 Step 2: Normalizing and storing articles...")
        try:
            stored_count, _ = normalize_and_store(all_articles, db)
            stats["articles_stored"] = stored_count
            logger.info(f"✅ Stored {stored_count} articles")
        except Exception as e:
            logger.error(f"❌ Normalization failed: {e}")
            stats["errors"].append(f"Normalization: {str(e)}")
            return stats
        
        # Step 3: Cluster articles (lightweight - only if we have articles)
        if stored_count > 0:
            logger.info("🔗 Step 3: Clustering articles...")
            try:
                events_created = cluster_articles(db)
                stats["events_created"] = events_created
                logger.info(f"✅ Created {events_created} events")
            except Exception as e:
                logger.error(f"❌ Clustering failed: {e}")
                stats["errors"].append(f"Clustering: {str(e)}")
        
        # Step 4: Score events (lightweight)
        if stats["events_created"] > 0:
            logger.info("📊 Step 4: Scoring events...")
            try:
                events_scored = score_recent_events(db, hours=24)
                stats["events_scored"] = events_scored
                logger.info(f"✅ Scored {events_scored} events")
            except Exception as e:
                logger.error(f"❌ Scoring failed: {e}")
                stats["errors"].append(f"Scoring: {str(e)}")
        
        db.close()
        
        # Calculate timing
        elapsed = time.time() - start_time
        stats["duration_seconds"] = round(elapsed, 2)
        
        logger.info(f"✅ Lightweight ingestion completed in {elapsed:.1f}s")
        logger.info(f"📊 Stats: {stats['articles_fetched']} fetched, {stats['articles_stored']} stored, {stats['events_created']} events, {stats['events_scored']} scored")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Lightweight ingestion failed: {e}")
        stats["errors"].append(f"Pipeline: {str(e)}")
        return stats


def run_lightweight_ingestion_with_timeout(timeout_seconds: int = 25) -> Dict:
    """
    Run lightweight ingestion with timeout for Render free tier.
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Ingestion timeout")
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = run_lightweight_ingestion()
        signal.alarm(0)  # Cancel timeout
        return result
    except TimeoutError:
        logger.error(f"⏰ Ingestion timed out after {timeout_seconds}s")
        return {
            "articles_fetched": 0,
            "articles_stored": 0,
            "events_created": 0,
            "events_scored": 0,
            "errors": ["Timeout"],
            "duration_seconds": timeout_seconds
        }
    finally:
        signal.alarm(0)  # Ensure timeout is cancelled
