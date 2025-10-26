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
from app.services.fetch.gdelt import fetch_gdelt_articles
from app.services.fetch.reddit import fetch_reddit_articles
from app.services.fetch.ngos_usgs_who_nasa_ocha import fetch_all_ngo_gov


def run_lightweight_ingestion() -> Dict:
    """
    Lightweight ingestion pipeline optimized for Render.

    Fetches from 5+ free sources that don't require API keys or billing:
    1. RSS feeds (Reuters, BBC, Guardian)
    2. NewsAPI (if key available)
    3. GDELT (breaking news, no key required)
    4. Reddit (news and worldnews subreddits)
    5. NGO/Gov sources (USGS earthquakes, WHO, UN OCHA, ReliefWeb)

    This ensures data ingestion works independently without external API dependencies.
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
            rss_articles = fetch_rss_articles()
            all_articles.extend(rss_articles)
            logger.info(f"✅ RSS: {len(rss_articles)} articles")
        except Exception as e:
            logger.error(f"❌ RSS failed: {e}")
            stats["errors"].append(f"RSS: {str(e)}")
        
        # NewsAPI (if key available)
        if settings.newsapi_key:
            try:
                newsapi_articles = fetch_newsapi_articles()
                all_articles.extend(newsapi_articles)
                logger.info(f"✅ NewsAPI: {len(newsapi_articles)} articles")
            except Exception as e:
                logger.error(f"❌ NewsAPI failed: {e}")
                stats["errors"].append(f"NewsAPI: {str(e)}")

        # GDELT (no API key needed, breaking news)
        try:
            gdelt_articles = fetch_gdelt_articles()
            all_articles.extend(gdelt_articles)
            logger.info(f"✅ GDELT: {len(gdelt_articles)} articles")
        except Exception as e:
            logger.error(f"❌ GDELT failed: {e}")
            stats["errors"].append(f"GDELT: {str(e)}")

        # Reddit (no API key needed)
        try:
            reddit_articles = fetch_reddit_articles()
            all_articles.extend(reddit_articles)
            logger.info(f"✅ Reddit: {len(reddit_articles)} articles")
        except Exception as e:
            logger.error(f"❌ Reddit failed: {e}")
            stats["errors"].append(f"Reddit: {str(e)}")

        # NGO/Government sources (USGS earthquakes, WHO, UN OCHA, ReliefWeb - no keys needed)
        try:
            ngo_articles = fetch_all_ngo_gov()
            all_articles.extend(ngo_articles)
            logger.info(f"✅ NGO/Gov sources: {len(ngo_articles)} articles")
        except Exception as e:
            logger.error(f"❌ NGO/Gov failed: {e}")
            stats["errors"].append(f"NGO/Gov: {str(e)}")

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
        
        # Step 3: Create events from articles (lightweight - no clustering)
        # In lightweight mode, create one event per article for search functionality
        # This enables search while avoiding expensive DBSCAN clustering
        logger.info("📊 Step 3: Creating events from articles (lightweight mode)...")
        try:
            from datetime import datetime

            # Get recent articles (last 50 stored in this cycle)
            recent_articles = db.query(Article).order_by(Article.id.desc()).limit(50).all()
            events_created = 0

            for article in recent_articles:
                try:
                    # Create a simple event from the article
                    # Each article becomes one event in lightweight mode
                    event = Event(
                        summary=article.title or article.summary or "News article",
                        articles_count=1,  # Lightweight: each event is from single article
                        unique_sources=1,
                        truth_score=50.0,  # Default score for lightweight mode
                        first_seen=article.timestamp or datetime.utcnow(),
                        last_seen=article.timestamp or datetime.utcnow(),
                        languages_json='["en"]',
                        category="general",  # Default category for lightweight mode
                    )
                    db.add(event)
                    db.flush()
                    events_created += 1
                except Exception as e:
                    db.rollback()
                    logger.debug(f"Failed to create event for article {article.id}: {e}")

            db.commit()
            stats["events_created"] = events_created
            logger.info(f"✅ Created {events_created} events from recent articles")
        except Exception as e:
            db.rollback()
            logger.error(f"⚠️  Event creation failed: {e}")
            # Don't fail the whole pipeline, continue without events
            stats["events_created"] = 0

        # Step 4: Skip scoring in lightweight mode (too heavy for Render free tier)
        logger.info("⊘ Step 4: Skipping scoring/clustering in lightweight mode")
        stats["events_scored"] = 0

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
    Run lightweight ingestion with timeout protection.

    Note: signal.SIGALRM doesn't work in background threads (APScheduler),
    so we use threading.Timer as a fallback for monitoring.
    """
    import threading

    result_container = {}
    exception_container = {}

    def run_with_exception_handling():
        try:
            result_container['result'] = run_lightweight_ingestion()
        except Exception as e:
            exception_container['exception'] = e

    # Run ingestion in a thread with timeout monitoring
    thread = threading.Thread(target=run_with_exception_handling, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    # Check if thread is still running (timeout occurred)
    if thread.is_alive():
        logger.error(f"⏰ Ingestion timed out after {timeout_seconds}s (still running)")
        return {
            "articles_fetched": 0,
            "articles_stored": 0,
            "events_created": 0,
            "events_scored": 0,
            "errors": [f"Timeout after {timeout_seconds} seconds"],
            "duration_seconds": timeout_seconds
        }

    # Check for exceptions
    if exception_container:
        logger.error(f"❌ Ingestion failed with exception: {exception_container['exception']}")
        return {
            "articles_fetched": 0,
            "articles_stored": 0,
            "events_created": 0,
            "events_scored": 0,
            "errors": [str(exception_container['exception'])],
            "duration_seconds": timeout_seconds
        }

    # Return successful result
    return result_container.get('result', {
        "articles_fetched": 0,
        "articles_stored": 0,
        "events_created": 0,
        "events_scored": 0,
        "errors": ["Unknown error"],
        "duration_seconds": timeout_seconds
    })
