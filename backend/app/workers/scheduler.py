"""APScheduler worker for periodic ingestion pipeline"""

import json
from dataclasses import asdict
from datetime import datetime, timedelta

import requests
from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Article
from app.services.cluster import cluster_articles

# Import fetchers
from app.services.fetch.gdelt import fetch_gdelt_articles
from app.services.fetch.mediastack import fetch_mediastack_articles
from app.services.fetch.newsapi import fetch_newsapi_articles
from app.services.fetch.ngos_usgs_who_nasa_ocha import fetch_all_ngo_gov
from app.services.fetch.reddit import fetch_reddit_articles
from app.services.fetch.rss import fetch_rss_articles

# Import processors
from app.services.fact_check import FactChecker
from app.services.normalize import normalize_and_store
from app.services.score import score_recent_events
from app.services.underreported import detect_underreported
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session


def send_discord_alert(message: str) -> None:
    """Send alert to Discord webhook (if configured)"""
    if not settings.discord_webhook_url:
        return

    try:
        payload = {"content": f"🚨 Truth Layer Alert: {message}"}
        requests.post(settings.discord_webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")


def cleanup_old_articles(db: Session) -> int:
    """Delete articles older than retention period"""
    cutoff = datetime.utcnow() - timedelta(days=settings.article_retention_days)

    deleted = (
        db.query(Article).filter(Article.ingested_at < cutoff).delete(synchronize_session=False)
    )

    db.commit()

    if deleted > 0:
        print(f"🗑️  Cleaned up {deleted} old articles (>{settings.article_retention_days} days)")

    return deleted


def run_fact_check_pipeline(db: Session, max_articles: int = 50) -> tuple[int, int]:
    """
    Fact-check recent unchecked articles.
    
    Args:
        db: Database session
        max_articles: Maximum number of articles to check per run (to avoid API limits)
        
    Returns:
        Tuple of (checked_count, flagged_count)
    """
    fact_checker = FactChecker()
    
    # Check if API key is configured
    if not fact_checker.google_api_key:
        print("⚠️  Google Fact Check API key not configured, skipping fact-checking")
        return 0, 0
    
    # Get recent unchecked articles
    articles = (
        db.query(Article)
        .filter(Article.fact_check_status == None)
        .order_by(Article.timestamp.desc())
        .limit(max_articles)
        .all()
    )
    
    if not articles:
        return 0, 0
    
    checked = 0
    flagged = 0
    
    for article in articles:
        try:
            # Run fact-checking
            status, flags = fact_checker.check_article(
                title=article.title,
                summary=article.summary or "",
                url=article.url,
                source=article.source
            )
            
            # Store results
            article.fact_check_status = status
            
            if flags:
                flags_data = [asdict(f) for f in flags]
                article.fact_check_flags_json = json.dumps(flags_data)
                flagged += 1
                
                # Send alert for flagged content
                if status == "false":
                    send_discord_alert(
                        f"❌ False claim detected: {article.title[:80]}... "
                        f"({len(flags)} flags)"
                    )
            else:
                article.fact_check_flags_json = None
            
            db.commit()
            checked += 1
            
        except Exception as e:
            print(f"⚠️  Error fact-checking article {article.id}: {e}")
            # Mark as unverified on error to avoid re-checking
            article.fact_check_status = "unverified"
            db.commit()
            continue
    
    return checked, flagged


def run_ingestion_pipeline() -> None:
    """
    Main ingestion pipeline job.

    Steps:
        1. Fetch from all sources
        2. Normalize and store
        3. Cluster articles
        4. Score events
        5. Detect underreported
        6. Fact-check articles
        7. Cleanup old data
    """
    start_time = datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"🔄 Starting ingestion pipeline at {start_time.isoformat()}")
    print(f"{'='*60}\n")

    db = SessionLocal()

    try:
        # Step 1: Fetch from all sources
        print("📥 Step 1: Fetching articles from all sources...")

        all_articles = []

        # GDELT
        all_articles.extend(fetch_gdelt_articles(minutes=15))

        # RSS feeds
        all_articles.extend(fetch_rss_articles())

        # Reddit
        all_articles.extend(fetch_reddit_articles())

        # Optional APIs
        all_articles.extend(fetch_newsapi_articles())
        all_articles.extend(fetch_mediastack_articles())

        # NGO/Gov sources
        all_articles.extend(fetch_all_ngo_gov())

        print(f"\n📊 Total articles fetched: {len(all_articles)}\n")

        # Step 2: Normalize and store
        print("🔧 Step 2: Normalizing and storing articles...")
        stored, duplicates = normalize_and_store(all_articles, db)
        print(f"✅ Stored: {stored}, Duplicates: {duplicates}\n")

        # Step 3: Cluster articles
        print("🔗 Step 3: Clustering articles into events...")
        events_created = cluster_articles(db)
        print(f"✅ Events created: {events_created}\n")

        # Step 4: Score events
        print("📊 Step 4: Scoring events...")
        events_scored = score_recent_events(db, hours=24)
        print(f"✅ Events scored: {events_scored}\n")

        # Step 5: Detect underreported
        print("🔍 Step 5: Detecting underreported events...")
        underreported_count = detect_underreported(db)
        print(f"✅ Underreported events: {underreported_count}\n")

        # Step 6: Fact-check articles
        print("🔍 Step 6: Fact-checking new articles...")
        fact_checked, flagged = run_fact_check_pipeline(db)
        print(f"✅ Fact-checked: {fact_checked}, Flagged: {flagged}\n")

        # Step 7: Cleanup
        print("🗑️  Step 7: Cleaning up old articles...")
        cleanup_old_articles(db)

        # Success summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{'='*60}")
        print(f"✅ Pipeline completed successfully in {duration:.1f}s")
        print(f"{'='*60}\n")

    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        print(f"❌ {error_msg}")
        send_discord_alert(error_msg)
        raise

    finally:
        db.close()


def main():
    """Main worker entry point"""
    print("🚀 Truth Layer Worker Starting...")
    db_info = settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
    print(f"Database: {db_info}")
    print(f"Ingestion interval: 15 minutes")
    print(f"Clustering window: {settings.clustering_window_hours} hours")
    print(f"Article retention: {settings.article_retention_days} days\n")

    # Initialize database
    init_db()

    # Create scheduler
    scheduler = BlockingScheduler()

    # Add job: run every 15 minutes
    scheduler.add_job(
        run_ingestion_pipeline,
        trigger=IntervalTrigger(minutes=15),
        id="ingestion_pipeline",
        name="Ingestion Pipeline",
        replace_existing=True,
    )

    # Run once immediately
    print("Running initial ingestion...")
    try:
        run_ingestion_pipeline()
    except Exception as e:
        print(f"Initial run failed: {e}")

    # Start scheduler
    print("\n✅ Worker started. Waiting for scheduled jobs...")
    print("Press Ctrl+C to exit.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Worker shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
