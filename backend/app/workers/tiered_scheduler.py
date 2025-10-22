"""
Optimized tiered ingestion pipeline with intelligent scheduling.

Separates ingestion into 5 tiers:
- TIER 1: Fast fetch (GDELT only) - 10/20 min
- TIER 2: Standard fetch (NewsAPI, RSS, Reddit) - 15/30 min
- TIER 3: Analysis (embeddings, conflict re-eval) - 60 min
- TIER 4: Deep analysis (fact-check, importance) - 240 min
- TIER 5: Maintenance (cleanup) - daily 3 AM

Memory optimized: processes articles in focused batches, no redundant embeddings.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from loguru import logger

from app.config import settings
from app.core.retry_utils import RetryConfig, get_retry_config_for_source, retry_with_backoff
from app.db import SessionLocal, init_db
from app.models import Article, Event
from app.services.cluster import cluster_articles
from app.services.fact_check import FactChecker
from app.services.normalize import normalize_and_store
from app.services.score import score_recent_events
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

# Source importance ranking for fetching
SOURCE_PRIORITY = {
    "GDELT": 1,      # Highest - real-time, breaking news
    "NewsAPI": 2,    # High - structured news data
    "RSS": 2,        # High - diverse sources
    "Reddit": 3,     # Medium - public sentiment
    "Mediastack": 3, # Medium - aggregator
    "NGO/Gov": 4,    # Lower - slower updates
}

pipeline_metrics: Dict = {
    "tier1_runs": 0,
    "tier2_runs": 0,
    "tier3_runs": 0,
    "tier4_runs": 0,
    "last_run": None,
}


def is_peak_hours() -> bool:
    """Check if current time is within peak hours"""
    current_hour = datetime.now().hour
    return settings.peak_hours_start <= current_hour < settings.peak_hours_end


def log_tier_metrics(tier: int, duration: float, items: int = 0, extra: str = ""):
    """Log tier execution metrics"""
    status = "⚡" if duration < 10 else "⏱️" if duration < 30 else "⚠️"
    msg = f"{status} TIER {tier}: {duration:.1f}s"
    if items:
        msg += f" ({items} items)"
    if extra:
        msg += f" {extra}"
    logger.info(msg)


def send_alert(message: str):
    """Send Discord alert if configured"""
    if not settings.discord_webhook_url:
        return
    try:
        requests.post(
            settings.discord_webhook_url,
            json={"content": f"🚨 Truth Layer: {message}"},
            timeout=5
        )
    except Exception as e:
        logger.debug(f"Alert send failed: {e}")


# ============================================================================
# TIER 1: Fast fetch (GDELT only, high velocity)
# ============================================================================

def run_tier1_fast_fetch() -> Tuple[int, int]:
    """
    TIER 1: Fetch from GDELT only (highest velocity breaking news).

    - Runs every 10 min (peak) / 20 min (off-peak)
    - Uses short time window to catch breaking stories
    - Minimal processing, direct to DB
    - Feeds into clustering asynchronously

    Returns: (articles_fetched, articles_stored)
    """
    from app.services.fetch.gdelt import fetch_gdelt_articles

    start = time.time()
    db = SessionLocal()

    try:
        # Use short window - only last 10 minutes of articles
        window = settings.tier1_interval_peak if is_peak_hours() else settings.tier1_interval_offpeak

        articles = fetch_gdelt_articles(minutes=window)
        logger.debug(f"GDELT fetched {len(articles)} articles")

        if articles:
            stored, dups = normalize_and_store(articles, db)
            log_tier_metrics(1, time.time() - start, stored, f"({dups} dups)")
            pipeline_metrics["tier1_runs"] += 1
            return len(articles), stored
        else:
            log_tier_metrics(1, time.time() - start, 0, "(no new articles)")
            return 0, 0

    except Exception as e:
        logger.error(f"TIER 1 failed: {type(e).__name__}: {str(e)}")
        send_alert(f"TIER 1 (GDELT) failed: {str(e)}")
        return 0, 0
    finally:
        db.close()


# ============================================================================
# TIER 2: Standard fetch (NewsAPI, RSS, Reddit)
# ============================================================================

def fetch_tier2_source(source_name: str, fetcher) -> Tuple[str, List[Dict], Optional[Exception]]:
    """Fetch from a single TIER 2 source with retry logic"""
    config = get_retry_config_for_source(source_name)
    try:
        articles = retry_with_backoff(
            fetcher,
            config=config,
            operation_name=f"tier2_{source_name}",
        )
        return source_name, articles, None
    except Exception as e:
        logger.warning(f"TIER 2 {source_name} failed: {type(e).__name__}")
        return source_name, [], e


def run_tier2_standard_fetch() -> Tuple[int, int]:
    """
    TIER 2: Fetch from main news sources (NewsAPI, RSS, Reddit).

    - Runs every 15 min (peak) / 30 min (off-peak)
    - Parallel fetching from 3-4 sources
    - Standard clustering and basic scoring
    - Skips heavy analysis (done in TIER 3)

    Returns: (articles_fetched, articles_stored)
    """
    from app.services.fetch.newsapi import fetch_newsapi_articles
    from app.services.fetch.rss import fetch_rss_articles
    from app.services.fetch.reddit import fetch_reddit_articles

    start = time.time()
    db = SessionLocal()
    all_articles = []

    try:
        # Use 15-minute window (standard news cycle)
        sources = [
            ("NewsAPI", fetch_newsapi_articles),
            ("RSS", fetch_rss_articles),
            ("Reddit", fetch_reddit_articles),
        ]

        # Parallel fetch with 30s per source
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(fetch_tier2_source, name, fetcher): name
                for name, fetcher in sources
            }

            for future in as_completed(futures, timeout=45):
                try:
                    source_name, articles, error = future.result(timeout=30)
                    all_articles.extend(articles)
                    status = "✓" if not error else "✗"
                    logger.debug(f"  {status} {source_name}: {len(articles)} articles")
                except Exception as e:
                    logger.warning(f"Tier 2 result error: {type(e).__name__}")

        if all_articles:
            stored, dups = normalize_and_store(all_articles, db)
            events = cluster_articles(db)  # Light clustering

            log_tier_metrics(
                2, time.time() - start, stored,
                f"({events} events, {dups} dups)"
            )
            pipeline_metrics["tier2_runs"] += 1
            return len(all_articles), stored
        else:
            log_tier_metrics(2, time.time() - start, 0)
            return 0, 0

    except Exception as e:
        logger.error(f"TIER 2 failed: {type(e).__name__}: {str(e)}")
        send_alert(f"TIER 2 (standard fetch) failed: {str(e)}")
        return 0, 0
    finally:
        db.close()


# ============================================================================
# TIER 3: Analysis (embeddings, conflict analysis)
# ============================================================================

def run_tier3_analysis() -> Tuple[int, int, int]:
    """
    TIER 3: Embedding-based analysis and conflict detection.

    - Runs every 60 minutes (all hours)
    - Re-evaluates narrative coherence for recent events (6-hour window)
    - Extracts representative excerpts for conflicts
    - Memory-efficient: processes max 100 articles per run

    Returns: (reevaluated_events, developing_excerpts, conflict_excerpts)
    """
    from app.services.coherence import (
        calculate_narrative_coherence,
        generate_conflict_explanation,
        group_by_political_bias,
        has_political_diversity,
        identify_narrative_perspectives,
    )
    from app.services.embed import generate_embeddings

    start = time.time()
    db = SessionLocal()
    stats = {"reevaluated": 0, "developing": 0, "conflict": 0}

    try:
        # Step 1: Re-evaluate conflicts for recent events (6-hour window)
        cutoff = datetime.utcnow() - timedelta(hours=settings.conflict_reevaluation_hours)
        events = (
            db.query(Event)
            .filter(Event.last_seen >= cutoff)
            .filter(Event.articles_count >= 3)
            .order_by(Event.last_seen.desc())
            .limit(25)  # Cap at 25 events to manage memory
            .all()
        )

        for event in events:
            try:
                old_severity = event.conflict_severity or "none"

                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles:
                    continue

                # Generate embeddings for this event's articles
                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                new_coherence, new_severity, explanation = calculate_narrative_coherence(
                    articles, embeddings
                )

                # Update if changed
                if old_severity != new_severity:
                    event.coherence_score = new_coherence
                    event.conflict_severity = new_severity
                    event.has_conflict = new_severity != "none"
                    if explanation:
                        event.conflict_explanation_json = json.dumps(asdict(explanation))
                    stats["reevaluated"] += 1
                    db.commit()

            except Exception as e:
                logger.debug(f"Event {event.id} re-eval failed: {type(e).__name__}")
                continue

        # Step 2: Extract excerpts for developing events (memory-safe)
        developing = (
            db.query(Event)
            .filter(Event.truth_score >= 40, Event.truth_score < 75)
            .filter(Event.conflict_explanation_json != None)
            .order_by(Event.last_seen.desc())
            .limit(settings.max_excerpts_per_run)
            .all()
        )

        for event in developing:
            try:
                explanation = json.loads(event.conflict_explanation_json)
                if any(p.get("representative_excerpts") for p in explanation.get("perspectives", [])):
                    continue

                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles:
                    continue

                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                if has_political_diversity(articles):
                    perspectives, articles_by_perspective = group_by_political_bias(articles)
                else:
                    perspectives, articles_by_perspective = identify_narrative_perspectives(
                        articles, embeddings
                    )

                updated = generate_conflict_explanation(
                    perspectives,
                    articles_by_perspective,
                    force_excerpt_extraction=True
                )

                event.conflict_explanation_json = json.dumps(asdict(updated))
                db.commit()
                stats["developing"] += 1

            except Exception as e:
                logger.debug(f"Developing excerpt {event.id} failed: {type(e).__name__}")
                continue

        # Step 3: Extract excerpts for conflict events
        conflicts = (
            db.query(Event)
            .filter(Event.has_conflict == True)
            .filter(Event.conflict_explanation_json != None)
            .order_by(Event.importance_score.desc())
            .limit(settings.max_excerpts_per_run)
            .all()
        )

        for event in conflicts:
            try:
                explanation = json.loads(event.conflict_explanation_json)
                if any(p.get("representative_excerpts") for p in explanation.get("perspectives", [])):
                    continue

                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if len(articles) < 2:
                    continue

                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                if has_political_diversity(articles):
                    perspectives, articles_by_perspective = group_by_political_bias(articles)
                else:
                    perspectives, articles_by_perspective = identify_narrative_perspectives(
                        articles, embeddings
                    )

                updated = generate_conflict_explanation(
                    perspectives,
                    articles_by_perspective,
                    force_excerpt_extraction=True
                )

                event.conflict_explanation_json = json.dumps(asdict(updated))
                db.commit()
                stats["conflict"] += 1

            except Exception as e:
                logger.debug(f"Conflict excerpt {event.id} failed: {type(e).__name__}")
                continue

        log_tier_metrics(
            3, time.time() - start, stats["reevaluated"] + stats["developing"] + stats["conflict"],
            f"(re-eval:{stats['reevaluated']} dev:{stats['developing']} conf:{stats['conflict']})"
        )
        pipeline_metrics["tier3_runs"] += 1
        return stats["reevaluated"], stats["developing"], stats["conflict"]

    except Exception as e:
        logger.error(f"TIER 3 failed: {type(e).__name__}: {str(e)}")
        send_alert(f"TIER 3 (analysis) failed: {str(e)}")
        return 0, 0, 0
    finally:
        db.close()


# ============================================================================
# TIER 4: Deep analysis (fact-checking, importance)
# ============================================================================

def run_tier4_deep_analysis() -> Tuple[int, int]:
    """
    TIER 4: Expensive operations (fact-checking, importance scoring).

    - Runs every 4 hours
    - Fact-checks batch of 30 articles with 2 parallel workers
    - Updates importance scores
    - Allows heavier compute without impacting real-time ingestion

    Returns: (articles_checked, articles_flagged)
    """
    start = time.time()
    db = SessionLocal()

    try:
        fact_checker = FactChecker()
        if not fact_checker.google_api_key:
            logger.debug("Fact-check API not configured, skipping TIER 4")
            return 0, 0

        # Get unchecked articles, capped at batch size
        unchecked = (
            db.query(Article)
            .filter(Article.fact_check_status == None)
            .order_by(Article.timestamp.desc())
            .limit(settings.fact_check_batch_size)
            .all()
        )

        if not unchecked:
            log_tier_metrics(4, time.time() - start, 0, "(no unchecked articles)")
            return 0, 0

        checked = 0
        flagged = 0

        # Parallel fact-checking with reduced workers
        with ThreadPoolExecutor(max_workers=settings.max_fact_check_workers) as executor:
            futures = {}
            for article in unchecked:
                def check_article(art):
                    try:
                        config = RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=10.0)
                        status, flags = retry_with_backoff(
                            fact_checker.check_article,
                            title=art.title,
                            summary=art.summary or "",
                            url=art.url,
                            source=art.source,
                            config=config,
                            operation_name=f"tier4_factcheck_{art.id}",
                        )
                        return art.id, status, flags
                    except Exception as e:
                        return art.id, "unverified", None

                futures[executor.submit(check_article, article)] = article

            for future in as_completed(futures, timeout=180):  # 3-min overall timeout
                try:
                    article_id, status, flags = future.result(timeout=60)
                    article = db.query(Article).filter(Article.id == article_id).first()

                    if article:
                        article.fact_check_status = status
                        if flags:
                            article.fact_check_flags_json = json.dumps(
                                [asdict(f) for f in flags]
                            )
                            flagged += 1
                            if status == "false":
                                send_alert(f"❌ False claim detected: {article.title[:60]}")
                        db.commit()
                        checked += 1

                except Exception as e:
                    logger.debug(f"Fact-check result error: {type(e).__name__}")

        log_tier_metrics(
            4, time.time() - start, checked,
            f"({flagged} flagged)"
        )
        pipeline_metrics["tier4_runs"] += 1
        return checked, flagged

    except Exception as e:
        logger.error(f"TIER 4 failed: {type(e).__name__}: {str(e)}")
        send_alert(f"TIER 4 (deep analysis) failed: {str(e)}")
        return 0, 0
    finally:
        db.close()


# ============================================================================
# TIER 5: Maintenance (cleanup)
# ============================================================================

def run_tier5_cleanup():
    """
    TIER 5: Daily maintenance and cleanup.

    - Runs at 3 AM daily
    - Removes articles older than retention period
    - Optimizes indexes
    - Clears stale cache
    """
    start = time.time()
    db = SessionLocal()

    try:
        cutoff = datetime.utcnow() - timedelta(days=settings.article_retention_days)
        deleted = (
            db.query(Article)
            .filter(Article.ingested_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()

        log_tier_metrics(5, time.time() - start, deleted, "(articles deleted)")
        logger.info(f"TIER 5: Deleted {deleted} old articles")

    except Exception as e:
        logger.error(f"TIER 5 failed: {type(e).__name__}: {str(e)}")
    finally:
        db.close()


# ============================================================================
# Scheduler Setup
# ============================================================================

def main():
    """Start optimized tiered scheduler"""
    print("\n🚀 Truth Layer Tiered Scheduler Starting...")
    print("=" * 70)
    print(f"📊 Configuration:")
    print(f"   Peak hours: {settings.peak_hours_start}:00-{settings.peak_hours_end}:00")
    print(f"   TIER 1 (GDELT): {settings.tier1_interval_peak}min peak / {settings.tier1_interval_offpeak}min off-peak")
    print(f"   TIER 2 (News): {settings.tier2_interval_peak}min peak / {settings.tier2_interval_offpeak}min off-peak")
    print(f"   TIER 3 (Analysis): {settings.tier3_interval}min (all hours)")
    print(f"   TIER 4 (Deep): {settings.tier4_interval}min (all hours)")
    print(f"   TIER 5 (Cleanup): Daily 3:00 AM\n")

    init_db()
    scheduler = BlockingScheduler()

    # TIER 1: Fast fetch (adaptive interval)
    if is_peak_hours():
        tier1_interval = settings.tier1_interval_peak
    else:
        tier1_interval = settings.tier1_interval_offpeak

    scheduler.add_job(
        run_tier1_fast_fetch,
        trigger=IntervalTrigger(minutes=tier1_interval),
        id="tier1_gdelt",
        name="TIER 1: GDELT Fast Fetch",
    )

    # TIER 2: Standard fetch (adaptive interval)
    if is_peak_hours():
        tier2_interval = settings.tier2_interval_peak
    else:
        tier2_interval = settings.tier2_interval_offpeak

    scheduler.add_job(
        run_tier2_standard_fetch,
        trigger=IntervalTrigger(minutes=tier2_interval),
        id="tier2_news",
        name="TIER 2: Standard Fetch",
    )

    # TIER 3: Analysis (hourly, all hours)
    scheduler.add_job(
        run_tier3_analysis,
        trigger=IntervalTrigger(minutes=settings.tier3_interval),
        id="tier3_analysis",
        name="TIER 3: Analysis Pipeline",
    )

    # TIER 4: Deep analysis (every 4 hours)
    scheduler.add_job(
        run_tier4_deep_analysis,
        trigger=IntervalTrigger(minutes=settings.tier4_interval),
        id="tier4_deep",
        name="TIER 4: Deep Analysis",
    )

    # TIER 5: Cleanup (daily 3 AM)
    scheduler.add_job(
        run_tier5_cleanup,
        trigger=CronTrigger(hour=3, minute=0),
        id="tier5_cleanup",
        name="TIER 5: Maintenance",
    )

    print("✅ Scheduler configured with 5 tiers")
    print(f"   Next TIER 1 in {tier1_interval}min")
    print(f"   Next TIER 2 in {tier2_interval}min")
    print(f"   Next TIER 3 in {settings.tier3_interval}min")
    print(f"   Next TIER 4 in {settings.tier4_interval}min")
    print("   Press Ctrl+C to exit.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Scheduler shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
