"""Backfill script to add article excerpts to existing conflict events

This script processes events with conflicts but no excerpts, fetches article content,
and uses LLM to extract key differentiating quotes for each perspective.

Usage:
    python -m backend.backfill_perspective_excerpts [--limit N] [--batch-size N]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Article, Event
from app.services.coherence import (
    NarrativePerspective,
    generate_conflict_explanation,
    group_by_political_bias,
    identify_narrative_perspectives,
)
from loguru import logger


def backfill_excerpts(limit: int = None, batch_size: int = 5, dry_run: bool = False):
    """
    Backfill excerpts for events with conflicts but no excerpts.
    
    Args:
        limit: Maximum number of events to process (None = all)
        batch_size: Number of events to process before pausing
        dry_run: If True, don't save changes to database
    """
    logger.info("Starting excerpt backfill process...")
    
    db = next(get_db())
    
    try:
        # Find events with conflicts but no excerpts
        query = select(Event).where(
            Event.has_conflict == True,
            Event.conflict_explanation_json.isnot(None),
        )
        
        if limit:
            query = query.limit(limit)
        
        events = db.execute(query).scalars().all()
        
        logger.info(f"Found {len(events)} conflict events to process")
        
        processed = 0
        updated = 0
        skipped = 0
        failed = 0
        
        for event in events:
            try:
                # Parse existing conflict explanation
                conflict_data = json.loads(event.conflict_explanation_json)
                perspectives_data = conflict_data.get("perspectives", [])
                
                # Check if excerpts already exist
                has_excerpts = any(
                    p.get("representative_excerpts") for p in perspectives_data
                )
                
                if has_excerpts:
                    logger.debug(f"Event {event.id} already has excerpts, skipping")
                    skipped += 1
                    continue
                
                logger.info(f"Processing event {event.id}: {event.summary[:60]}...")
                
                # Fetch articles for this event
                articles_query = select(Article).where(Article.cluster_id == event.id)
                articles = db.execute(articles_query).scalars().all()
                
                if not articles:
                    logger.warning(f"No articles found for event {event.id}")
                    skipped += 1
                    continue
                
                # Reconstruct perspectives with articles
                # We need to re-group articles to match the existing perspectives
                perspectives_with_articles = reconstruct_perspective_groups(
                    articles, perspectives_data
                )
                
                if not perspectives_with_articles:
                    logger.warning(f"Could not reconstruct perspectives for event {event.id}")
                    skipped += 1
                    continue
                
                perspectives, articles_by_perspective = perspectives_with_articles
                
                # Generate new conflict explanation with excerpts
                new_explanation = generate_conflict_explanation(
                    perspectives, articles_by_perspective
                )
                
                # Check if excerpts were successfully extracted
                new_perspectives = new_explanation.perspectives
                extracted_count = sum(
                    1 for p in new_perspectives if p.get("representative_excerpts")
                )
                
                if extracted_count == 0:
                    logger.warning(f"No excerpts extracted for event {event.id}")
                    failed += 1
                else:
                    logger.success(
                        f"Extracted excerpts for {extracted_count}/{len(perspectives)} perspectives"
                    )
                    
                    # Update event with new explanation
                    if not dry_run:
                        event.conflict_explanation_json = json.dumps({
                            "perspectives": new_explanation.perspectives,
                            "key_difference": new_explanation.key_difference,
                            "difference_type": new_explanation.difference_type,
                        })
                        db.commit()
                    
                    updated += 1
                
                processed += 1
                
                # Pause between batches to avoid rate limits
                if processed % batch_size == 0:
                    logger.info(
                        f"Processed {processed} events. Pausing for 5 seconds..."
                    )
                    time.sleep(5)
                
            except Exception as e:
                logger.error(f"Failed to process event {event.id}: {e}")
                failed += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"Backfill complete!")
        logger.info(f"  Total processed: {processed}")
        logger.info(f"  Successfully updated: {updated}")
        logger.info(f"  Skipped (already had excerpts): {skipped}")
        logger.info(f"  Failed: {failed}")
        
        if dry_run:
            logger.info("DRY RUN - No changes saved to database")
        
    finally:
        db.close()


def reconstruct_perspective_groups(
    articles: list[Article], perspectives_data: list[dict]
) -> tuple[list[NarrativePerspective], list[list[Article]]] | None:
    """
    Reconstruct perspective groups by matching articles to perspectives.
    
    Args:
        articles: List of articles in the event
        perspectives_data: Existing perspective data from conflict explanation
        
    Returns:
        Tuple of (perspectives, articles_by_perspective) or None if reconstruction fails
    """
    try:
        # Check if perspectives have political_leaning (indicates political grouping)
        has_political_grouping = any(
            p.get("political_leaning") for p in perspectives_data
        )
        
        if has_political_grouping:
            # Use political grouping
            perspectives, articles_by_perspective = group_by_political_bias(articles)
        else:
            # Match articles to perspectives by source domain
            perspectives = []
            articles_by_perspective = []
            
            for persp_data in perspectives_data:
                perspective_sources = set(persp_data.get("sources", []))
                
                # Find articles matching these sources
                matching_articles = [
                    article
                    for article in articles
                    if extract_domain(article.source) in perspective_sources
                ]
                
                if matching_articles:
                    # Create NarrativePerspective from data
                    perspective = NarrativePerspective(
                        sources=persp_data.get("sources", []),
                        article_count=persp_data.get("article_count", 0),
                        representative_title=persp_data.get("representative_title", ""),
                        key_entities=persp_data.get("key_entities", []),
                        sentiment=persp_data.get("sentiment", "neutral"),
                        focus_keywords=persp_data.get("focus_keywords", []),
                        political_leaning=persp_data.get("political_leaning"),
                    )
                    perspectives.append(perspective)
                    articles_by_perspective.append(matching_articles)
        
        if perspectives and articles_by_perspective:
            return perspectives, articles_by_perspective
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to reconstruct perspectives: {e}")
        return None


def extract_domain(source: str) -> str:
    """Extract clean domain from source URL or string."""
    from urllib.parse import urlparse
    
    if source.startswith("http"):
        parsed = urlparse(source)
        domain = parsed.netloc
    else:
        domain = source
    
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    
    return domain


def main():
    parser = argparse.ArgumentParser(
        description="Backfill article excerpts for conflict events"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of events to process (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of events to process before pausing (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save changes to database",
    )
    
    args = parser.parse_args()
    
    backfill_excerpts(
        limit=args.limit,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

