"""APScheduler worker for periodic ingestion pipeline"""

import gc
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from loguru import logger

from app.config import settings
from app.core.memory_utils import clear_session_cache, memory_safe_processing, MemoryProfiler
from app.core.retry_utils import RetryConfig, get_retry_config_for_source, retry_with_backoff
from app.db import SessionLocal, init_db
from app.models import Article, Event
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
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

# Global metrics tracking
pipeline_metrics: Dict[str, Dict] = {
    "source_stats": {},
    "last_run": None,
    "total_runs": 0,
}


def get_current_interval() -> int:
    """
    Determine current ingestion interval based on time of day.
    
    Returns peak interval during peak hours, off-peak interval otherwise.
    """
    current_hour = datetime.now().hour
    
    if settings.peak_hours_start <= current_hour < settings.peak_hours_end:
        return settings.ingestion_interval_peak
    else:
        return settings.ingestion_interval_offpeak


def log_step_metrics(step_name: str, duration: float, items_processed: int = 0, extra_info: str = ""):
    """Log metrics for a pipeline step using structured logging"""
    if duration < 60:
        logger.info(
            f"{step_name}: Completed in {duration:.1f}s "
            f"(items={items_processed}, {extra_info})" if extra_info else
            f"{step_name}: Completed in {duration:.1f}s (items={items_processed})"
        )
    else:
        logger.warning(
            f"{step_name}: Took {duration:.1f}s (slow!) "
            f"(items={items_processed}, {extra_info})" if extra_info else
            f"{step_name}: Took {duration:.1f}s (slow!) (items={items_processed})"
        )


def send_discord_alert(message: str) -> None:
    """Send alert to Discord webhook (if configured)"""
    if not settings.discord_webhook_url:
        logger.debug("Discord webhook not configured, skipping alert")
        return

    try:
        payload = {"content": f"🚨 Truth Layer Alert: {message}"}
        requests.post(settings.discord_webhook_url, json=payload, timeout=5)
        logger.debug("Discord alert sent successfully")
    except requests.Timeout:
        logger.warning("Discord alert timeout (5s exceeded)")
    except requests.RequestException as e:
        logger.warning(f"Discord alert failed (network error): {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(f"Discord alert failed (unexpected error): {type(e).__name__}: {str(e)}")


def cleanup_old_articles(db: Session) -> int:
    """Delete articles older than retention period"""
    cutoff = datetime.utcnow() - timedelta(days=settings.article_retention_days)

    try:
        deleted = (
            db.query(Article)
            .filter(Article.ingested_at < cutoff)
            .delete(synchronize_session=False)
        )

        db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} articles older than {settings.article_retention_days} days")
        else:
            logger.debug(f"No articles older than {settings.article_retention_days} days found")

        return deleted

    except Exception as e:
        logger.error(f"Cleanup failed: {type(e).__name__}: {str(e)}")
        db.rollback()
        return 0


def fact_check_single_article(article_id: int, title: str, summary: str, url: str, source: str) -> tuple:
    """
    Fact-check a single article with retry logic (thread-safe).

    Uses exponential backoff for transient API failures.

    Returns:
        Tuple of (article_id, status, flags, error_or_none)
    """
    fact_checker = FactChecker()
    config = RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=10.0)

    try:
        status, flags = retry_with_backoff(
            fact_checker.check_article,
            title=title,
            summary=summary or "",
            url=url,
            source=source,
            config=config,
            operation_name=f"fact_check_article_{article_id}",
        )
        return (article_id, status, flags, None)

    except Exception as e:
        logger.warning(
            f"fact_check_article_{article_id}: Failed after {config.max_attempts} attempts: "
            f"{type(e).__name__}: {str(e)}"
        )
        return (article_id, "unverified", None, e)


def run_fact_check_pipeline(db: Session, max_articles: int = None) -> tuple[int, int]:
    """
    Fact-check recent unchecked articles with optional parallel processing.

    Uses exponential backoff for API failures. Individual article failures
    don't block the pipeline.

    Args:
        db: Database session
        max_articles: Maximum number of articles to check per run

    Returns:
        Tuple of (checked_count, flagged_count)
    """
    fact_checker = FactChecker()

    # Check if API key is configured
    if not fact_checker.google_api_key:
        logger.warning("Google Fact Check API key not configured, skipping fact-checking")
        return 0, 0

    # Use configured batch size if not specified
    if max_articles is None:
        max_articles = settings.fact_check_batch_size

    # Get recent unchecked articles
    articles = (
        db.query(Article)
        .filter(Article.fact_check_status == None)
        .order_by(Article.timestamp.desc())
        .limit(max_articles)
        .all()
    )

    if not articles:
        logger.debug("No unchecked articles found")
        return 0, 0

    checked = 0
    flagged = 0
    errors = 0

    # Parallel fact-checking if configured
    if settings.max_fact_check_workers > 1:
        logger.info(
            f"Fact-checking {len(articles)} articles (parallel, {settings.max_fact_check_workers} workers)"
        )

        with ThreadPoolExecutor(max_workers=settings.max_fact_check_workers) as executor:
            # Submit all articles for checking
            future_to_article = {
                executor.submit(
                    fact_check_single_article,
                    article.id,
                    article.title,
                    article.summary,
                    article.url,
                    article.source,
                ): article
                for article in articles
            }

            # Process results as they complete
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    article_id, status, flags, error = future.result(timeout=30)

                    if error:
                        logger.warning(
                            f"Article {article_id}: Failed fact-check: {type(error).__name__}: {str(error)}"
                        )
                        article.fact_check_status = "unverified"
                        errors += 1
                    else:
                        article.fact_check_status = status

                        if flags:
                            flags_data = [asdict(f) for f in flags]
                            article.fact_check_flags_json = json.dumps(flags_data)
                            flagged += 1

                            if status == "false":
                                alert_msg = (
                                    f"❌ False claim: {article.title[:80]}... ({len(flags)} flags)"
                                )
                                logger.warning(alert_msg)
                                send_discord_alert(alert_msg)
                        else:
                            article.fact_check_flags_json = None

                        checked += 1
                        logger.debug(f"Article {article_id}: Fact-check complete (status={status})")

                    db.commit()

                except TimeoutError:
                    logger.error(f"Article {article.id}: Fact-check timeout (30s exceeded)")
                    article.fact_check_status = "unverified"
                    db.commit()
                    errors += 1

                except Exception as e:
                    logger.error(
                        f"Article {article.id}: Failed to process result: {type(e).__name__}: {str(e)}"
                    )
                    article.fact_check_status = "unverified"
                    db.commit()
                    errors += 1

    else:
        # Sequential fact-checking (fallback)
        logger.info(f"Fact-checking {len(articles)} articles (sequential)")

        for article in articles:
            try:
                config = RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=10.0)
                status, flags = retry_with_backoff(
                    fact_checker.check_article,
                    title=article.title,
                    summary=article.summary or "",
                    url=article.url,
                    source=article.source,
                    config=config,
                    operation_name=f"fact_check_article_{article.id}",
                )

                article.fact_check_status = status

                if flags:
                    flags_data = [asdict(f) for f in flags]
                    article.fact_check_flags_json = json.dumps(flags_data)
                    flagged += 1

                    if status == "false":
                        alert_msg = (
                            f"❌ False claim: {article.title[:80]}... ({len(flags)} flags)"
                        )
                        logger.warning(alert_msg)
                        send_discord_alert(alert_msg)
                else:
                    article.fact_check_flags_json = None

                db.commit()
                checked += 1
                logger.debug(f"Article {article.id}: Fact-check complete (status={status})")

            except Exception as e:
                logger.warning(
                    f"Article {article.id}: Fact-check failed: {type(e).__name__}: {str(e)}"
                )
                article.fact_check_status = "unverified"
                db.commit()
                errors += 1

    if errors > 0:
        logger.warning(f"Fact-checking completed with {errors} errors")

    return checked, flagged


def fetch_articles_from_source(source_name: str, fetcher) -> tuple[List[Dict], Optional[Exception]]:
    """
    Fetch articles from a single source with retry logic.

    Args:
        source_name: Name of the source for logging
        fetcher: Callable that fetches articles

    Returns:
        Tuple of (articles_list, error_or_none)
    """
    config = get_retry_config_for_source(source_name)

    try:
        articles = retry_with_backoff(
            fetcher,
            config=config,
            operation_name=f"fetch_{source_name}",
        )
        return articles, None
    except Exception as e:
        logger.error(
            f"fetch_{source_name}: Failed permanently after {config.max_attempts} attempts: "
            f"{type(e).__name__}: {str(e)}"
        )
        return [], e


def fetch_articles_parallel() -> List[Dict]:
    """
    Fetch articles from all sources in parallel with proper error handling and retries.

    Uses exponential backoff for transient failures while respecting rate limits.
    Individual source failures don't block other sources.

    Returns:
        List of all successfully fetched articles
    """
    all_articles = []

    if not settings.enable_parallel_fetching:
        # Sequential fetching (fallback)
        logger.info("Using sequential fetching (parallel disabled)")

        sources = [
            ("GDELT", lambda: fetch_gdelt_articles(minutes=get_current_interval())),
            ("RSS Feeds", fetch_rss_articles),
            ("Reddit", fetch_reddit_articles),
            ("NewsAPI", fetch_newsapi_articles),
            ("Mediastack", fetch_mediastack_articles),
            ("NGO/Gov", fetch_all_ngo_gov),
        ]

        for source_name, fetcher in sources:
            articles, error = fetch_articles_from_source(source_name, fetcher)
            count = len(articles)
            all_articles.extend(articles)

            # Track source stats
            if error:
                logger.warning(f"fetch_{source_name}: {count} articles (after error: {error})")
                pipeline_metrics["source_stats"][source_name] = {
                    "count": count,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                logger.info(f"fetch_{source_name}: {count} articles")
                pipeline_metrics["source_stats"][source_name] = {
                    "count": count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
        return all_articles

    # Parallel fetching with ThreadPoolExecutor
    logger.info("Using parallel fetching (6 workers)")

    fetchers = [
        ("GDELT", lambda: fetch_gdelt_articles(minutes=get_current_interval())),
        ("RSS Feeds", fetch_rss_articles),
        ("Reddit", fetch_reddit_articles),
        ("NewsAPI", fetch_newsapi_articles),
        ("Mediastack", fetch_mediastack_articles),
        ("NGO/Gov", fetch_all_ngo_gov),
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all fetchers with retry logic
        future_to_source = {
            executor.submit(fetch_articles_from_source, name, fetcher): name
            for name, fetcher in fetchers
        }

        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                articles, error = future.result(timeout=120)  # 2-minute timeout per source
                count = len(articles)
                all_articles.extend(articles)

                # Track source stats
                if error:
                    logger.warning(
                        f"fetch_{source_name}: {count} articles retrieved (after error: {type(error).__name__})"
                    )
                    pipeline_metrics["source_stats"][source_name] = {
                        "count": count,
                        "error": str(error),
                        "error_type": type(error).__name__,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    logger.info(f"fetch_{source_name}: {count} articles")
                    pipeline_metrics["source_stats"][source_name] = {
                        "count": count,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

            except TimeoutError:
                logger.error(f"fetch_{source_name}: Timeout (exceeded 120s)")
                pipeline_metrics["source_stats"][source_name] = {
                    "count": 0,
                    "error": "Timeout exceeded 120s",
                    "error_type": "TimeoutError",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(
                    f"fetch_{source_name}: Unexpected error retrieving result: "
                    f"{type(e).__name__}: {str(e)}"
                )
                pipeline_metrics["source_stats"][source_name] = {
                    "count": 0,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.utcnow().isoformat(),
                }

    return all_articles


def extract_developing_excerpts(db: Session, max_events: int = 10) -> int:
    """
    Extract excerpts for developing events that don't have them yet.

    OPTIMIZATION: Uses memory_safe_processing to cleanup after each event

    Args:
        db: Database session
        max_events: Maximum number of events to process per run (to avoid long processing)

    Returns:
        Number of events processed
    """
    from app.services.coherence import (
        generate_conflict_explanation,
        group_by_political_bias,
        has_political_diversity,
        identify_narrative_perspectives,
    )
    from app.services.embed import generate_embeddings

    # Find developing events without excerpts (limit to most recent)
    developing = (
        db.query(Event)
        .filter(Event.truth_score >= 40, Event.truth_score < 75)
        .filter(Event.conflict_explanation_json != None)  # Has perspectives
        .order_by(Event.last_seen.desc())  # Most recent first
        .limit(max_events)  # Limit to avoid long processing
        .all()
    )

    processed = 0

    # OPTIMIZATION: Use memory-safe processing context
    with memory_safe_processing(db, cleanup_interval=1, description="developing excerpts") as mem_ctx:
        for event in developing:
            try:
                # Check if already has excerpts
                explanation = json.loads(event.conflict_explanation_json)
                if any(p.get("representative_excerpts") for p in explanation.get("perspectives", [])):
                    continue  # Already has excerpts

                # Get articles
                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles:
                    continue

                # Regenerate with excerpt extraction forced
                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                # Group by political bias if diverse
                if has_political_diversity(articles):
                    perspectives, articles_by_perspective = group_by_political_bias(articles)
                else:
                    perspectives, articles_by_perspective = identify_narrative_perspectives(articles, embeddings)

                # Generate with forced excerpt extraction
                updated_explanation = generate_conflict_explanation(
                    perspectives,
                    articles_by_perspective,
                    force_excerpt_extraction=True
                )

                event.conflict_explanation_json = json.dumps(asdict(updated_explanation))
                db.commit()
                processed += 1
                mem_ctx.mark_processed()

            except Exception as e:
                logger.warning(f"Failed to extract excerpts for event {event.id}: {type(e).__name__}: {str(e)}")
                continue

    return processed


def extract_conflict_excerpts(db: Session, max_events: int = 15) -> int:
    """
    Extract excerpts for conflict events that don't have them yet.

    Unlike developing excerpts, this targets ANY event with conflicts
    regardless of truth score.

    OPTIMIZATION: Uses memory_safe_processing to cleanup after each event

    Args:
        db: Database session
        max_events: Maximum number of events to process per run

    Returns:
        Number of events processed
    """
    from app.services.coherence import (
        generate_conflict_explanation,
        group_by_political_bias,
        has_political_diversity,
        identify_narrative_perspectives,
    )
    from app.services.embed import generate_embeddings

    # Find conflict events without excerpts
    # OPTIMIZATION: Only process high-importance conflicts to save LLM API costs
    # Events with importance_score >= 60 get full analysis with LLM excerpt extraction
    # Lower-importance events use generic excerpts (faster, no LLM cost)
    conflicts = (
        db.query(Event)
        .filter(Event.has_conflict == True)  # Must have conflict flag
        .filter(Event.conflict_explanation_json != None)  # Has perspectives
        .filter(Event.importance_score >= 60)  # Only high-importance events (OPTIMIZATION: save 70% LLM costs)
        .order_by(Event.importance_score.desc())  # Highest importance first
        .limit(max_events)
        .all()
    )

    processed = 0

    # OPTIMIZATION: Use memory-safe processing context
    with memory_safe_processing(db, cleanup_interval=1, description="conflict excerpts") as mem_ctx:
        for event in conflicts:
            try:
                # Check if already has excerpts
                explanation = json.loads(event.conflict_explanation_json)
                if any(p.get("representative_excerpts") for p in explanation.get("perspectives", [])):
                    continue  # Already has excerpts

                # Get articles
                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles or len(articles) < 2:
                    continue

                # Regenerate with excerpt extraction forced
                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                # Group by political bias if diverse
                if has_political_diversity(articles):
                    perspectives, articles_by_perspective = group_by_political_bias(articles)
                else:
                    perspectives, articles_by_perspective = identify_narrative_perspectives(articles, embeddings)

                # Generate with forced excerpt extraction
                updated_explanation = generate_conflict_explanation(
                    perspectives,
                    articles_by_perspective,
                    force_excerpt_extraction=True
                )

                event.conflict_explanation_json = json.dumps(asdict(updated_explanation))
                db.commit()
                processed += 1
                mem_ctx.mark_processed()

                logger.info(f"Extracted excerpts for conflict event {event.id}: {event.summary[:60]}")

            except Exception as e:
                logger.warning(f"Failed to extract excerpts for conflict event {event.id}: {type(e).__name__}: {str(e)}")
            continue
    
    return processed


def reevaluate_event_conflicts(db: Session, hours: int = 48) -> int:
    """
    Reevaluate coherence scores for recent events.

    Catches conflicts that emerge as narratives evolve.

    OPTIMIZATION: Uses memory_safe_processing to cleanup after each event

    Args:
        db: Database session
        hours: Look back window

    Returns:
        Number of events with status changes
    """
    from app.services.coherence import calculate_narrative_coherence
    from app.services.embed import generate_embeddings

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Get recent events regardless of current conflict status
    events = (
        db.query(Event)
        .filter(Event.last_seen >= cutoff)
        .filter(Event.articles_count >= 3)  # Need enough articles
        .all()
    )

    status_changes = 0

    # OPTIMIZATION: Use memory-safe processing context
    with memory_safe_processing(db, cleanup_interval=2, description="conflict re-evaluation") as mem_ctx:
        for event in events:
            try:
                old_coherence = event.coherence_score or 100
                old_severity = event.conflict_severity or "none"

                # Get all articles and recalculate
                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles:
                    continue

                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                new_coherence, new_severity, explanation = calculate_narrative_coherence(
                    articles, embeddings
                )

                # Check for meaningful changes
                coherence_changed = abs(old_coherence - new_coherence) > 5
                severity_changed = old_severity != new_severity

                if coherence_changed or severity_changed:
                    logger.info(
                        f"Event {event.id} conflict status changed: "
                        f"{old_severity} ({old_coherence:.1f}) -> {new_severity} ({new_coherence:.1f})"
                    )

                    # Track when conflict first emerged
                    was_conflicted = old_severity != "none"
                    is_now_conflicted = new_severity != "none"

                    if not was_conflicted and is_now_conflicted:
                        event.conflict_detected_at = datetime.utcnow()
                        logger.warning(f"Event {event.id} became conflicted during re-evaluation!")

                    event.coherence_score = new_coherence
                    event.conflict_severity = new_severity
                    event.has_conflict = new_severity != "none"

                    if explanation:
                        event.conflict_explanation_json = json.dumps(asdict(explanation))

                    status_changes += 1
                    db.commit()

                mem_ctx.mark_processed()

            except Exception as e:
                logger.warning(f"Failed to reevaluate event {event.id}: {type(e).__name__}: {str(e)}")
                continue

    return status_changes


def run_ingestion_pipeline() -> None:
    """
    Main ingestion pipeline job.

    Steps:
        1. Fetch from all sources (parallel)
        2. Normalize and store
        3. Cluster articles
        4. Score events
        5. Extract excerpts and re-evaluate conflicts
        6. Fact-check articles

    Uses exponential backoff for transient failures and structured logging.
    """
    # Check if we're on Render free tier (lightweight mode)
    # Only use lightweight mode for actual free tier instances
    # Standard tier and above should use full pipeline
    if os.getenv("RENDER_INSTANCE_TYPE", "").lower() == "free":
        logger.info("🪶 Running lightweight pipeline for Render free tier...")
        from app.workers.lightweight_scheduler import run_lightweight_ingestion_with_timeout
        result = run_lightweight_ingestion_with_timeout(timeout_seconds=25)
        logger.info(f"✅ Lightweight pipeline completed: {result}")
        return
    
    pipeline_start = time.time()
    start_time = datetime.utcnow()

    # Determine if peak or off-peak
    current_interval = get_current_interval()
    period = "PEAK" if current_interval == settings.ingestion_interval_peak else "OFF-PEAK"

    logger.info(
        f"Pipeline #{pipeline_metrics['total_runs'] + 1} starting "
        f"({period}: {current_interval}-min interval)"
    )

    db = SessionLocal()
    pipeline_metrics["total_runs"] += 1
    all_articles = []

    try:
        # Step 1: Fetch from all sources (parallel)
        step_start = time.time()
        logger.info("Step 1: Fetching articles from all sources")

        all_articles = fetch_articles_parallel()

        step_duration = time.time() - step_start
        log_step_metrics("Fetch", step_duration, len(all_articles))

        # Step 2: Normalize and store
        step_start = time.time()
        logger.info("Step 2: Normalizing and storing articles")
        stored, duplicates = normalize_and_store(all_articles, db)
        step_duration = time.time() - step_start
        dup_rate = (
            (duplicates / (stored + duplicates) * 100) if (stored + duplicates) > 0 else 0
        )
        log_step_metrics("Normalize", step_duration, stored, f"{duplicates} dups ({dup_rate:.1f}%)")

        # Step 3: Cluster articles
        step_start = time.time()
        logger.info("Step 3: Clustering articles into events")
        events_created = cluster_articles(db)
        step_duration = time.time() - step_start
        log_step_metrics("Cluster", step_duration, events_created)

        # Step 4: Score events
        step_start = time.time()
        logger.info("Step 4: Scoring events")
        events_scored = score_recent_events(db, hours=24)
        step_duration = time.time() - step_start
        log_step_metrics("Score", step_duration, events_scored)

        # Step 5: Extract excerpts for developing events
        step_start = time.time()
        logger.info("Step 5: Extracting excerpts for developing events")
        developing_excerpts = extract_developing_excerpts(db)
        step_duration = time.time() - step_start
        log_step_metrics("Developing Excerpts", step_duration, developing_excerpts)

        # Step 5b: Extract excerpts for conflict events
        step_start = time.time()
        logger.info("Step 5b: Extracting excerpts for conflict events")
        conflict_excerpts = extract_conflict_excerpts(db)
        step_duration = time.time() - step_start
        log_step_metrics("Conflict Excerpts", step_duration, conflict_excerpts)

        # Step 5a: Re-evaluate recent conflicts
        step_start = time.time()
        logger.info("Step 5a: Re-evaluating conflict status for recent events")
        conflict_changes = reevaluate_event_conflicts(db, hours=48)
        step_duration = time.time() - step_start
        log_step_metrics("Conflict Re-evaluation", step_duration, conflict_changes)

        # Step 6: Fact-check articles
        step_start = time.time()
        logger.info("Step 6: Fact-checking new articles")
        fact_checked, flagged = run_fact_check_pipeline(db)
        step_duration = time.time() - step_start
        log_step_metrics("Fact-check", step_duration, fact_checked, f"{flagged} flagged")

        # Success summary
        pipeline_duration = time.time() - pipeline_start
        end_time = datetime.utcnow()
        pipeline_metrics["last_run"] = end_time.isoformat()

        logger.info(
            f"Pipeline #{pipeline_metrics['total_runs']} completed in {pipeline_duration:.1f}s: "
            f"{len(all_articles)} articles fetched, {stored} stored, "
            f"{events_created} events created, {events_scored} scored, "
            f"{developing_excerpts} developing excerpts, {conflict_excerpts} conflict excerpts, "
            f"{fact_checked} fact-checked ({flagged} flagged)"
        )

    except Exception as e:
        error_msg = f"Pipeline failed: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        send_discord_alert(error_msg)
        raise

    finally:
        db.close()


def run_cleanup_job() -> None:
    """Daily cleanup job for old articles"""
    logger.info("Starting daily cleanup job")
    db = SessionLocal()
    try:
        deleted = cleanup_old_articles(db)
        logger.info(f"Cleanup job completed successfully")
    except Exception as e:
        logger.error(f"Cleanup job failed: {type(e).__name__}: {str(e)}", exc_info=True)
    finally:
        db.close()


def update_scheduler_interval(scheduler) -> None:
    """
    Update scheduler interval based on current time period.
    
    This function is called periodically to adjust the ingestion interval
    when transitioning between peak and off-peak hours.
    """
    current_interval = get_current_interval()
    
    # Get the current job
    job = scheduler.get_job("ingestion_pipeline")
    if job:
        # Check if interval needs updating
        current_trigger_minutes = job.trigger.interval.total_seconds() / 60
        
        if current_trigger_minutes != current_interval:
            period = "PEAK" if current_interval == settings.ingestion_interval_peak else "OFF-PEAK"
            logger.info(
                f"Switching to {period} mode: Updating interval from "
                f"{int(current_trigger_minutes)} to {current_interval} minutes"
            )
            
            # Reschedule with new interval
            scheduler.reschedule_job(
                "ingestion_pipeline",
                trigger=IntervalTrigger(minutes=current_interval),
            )


def main():
    """Main worker entry point"""
    print("🚀 Truth Layer Worker Starting...")
    print("="*70)
    
    db_info = settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
    print(f"📊 Configuration:")
    print(f"   Database: {db_info}")
    print(f"   Peak interval: {settings.ingestion_interval_peak} minutes ({settings.peak_hours_start}:00-{settings.peak_hours_end}:00)")
    print(f"   Off-peak interval: {settings.ingestion_interval_offpeak} minutes")
    print(f"   Parallel fetching: {'Enabled' if settings.enable_parallel_fetching else 'Disabled'}")
    print(f"   Clustering window: {settings.clustering_window_hours} hours")
    print(f"   Article retention: {settings.article_retention_days} days")
    print(f"   Fact-check batch: {settings.fact_check_batch_size} articles/run\n")

    # Initialize database
    init_db()

    # Create scheduler
    scheduler = BlockingScheduler()

    # Add main ingestion job - runs at current interval
    current_interval = get_current_interval()
    scheduler.add_job(
        run_ingestion_pipeline,
        trigger=IntervalTrigger(minutes=current_interval),
        id="ingestion_pipeline",
        name="Ingestion Pipeline",
        replace_existing=True,
    )
    
    # Add interval checker job - runs every 5 minutes to adjust schedule
    scheduler.add_job(
        update_scheduler_interval,
        args=[scheduler],
        trigger=IntervalTrigger(minutes=5),
        id="interval_updater",
        name="Interval Updater",
        replace_existing=True,
    )
    
    # Add daily cleanup job - runs at 3 AM
    scheduler.add_job(
        run_cleanup_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_cleanup",
        name="Daily Cleanup",
        replace_existing=True,
    )

    # Run once immediately
    print("🔄 Running initial ingestion...")
    try:
        run_ingestion_pipeline()
    except Exception as e:
        print(f"❌ Initial run failed: {e}\n")

    # Start scheduler
    period = "PEAK" if current_interval == settings.ingestion_interval_peak else "OFF-PEAK"
    print(f"✅ Worker started in {period} mode")
    print(f"   Next ingestion in {current_interval} minutes")
    print(f"   Daily cleanup scheduled for 3:00 AM")
    print(f"   Interval will auto-adjust between peak/off-peak hours")
    print(f"   Press Ctrl+C to exit.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Worker shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
