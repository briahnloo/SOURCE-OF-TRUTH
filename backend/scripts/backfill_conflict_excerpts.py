"""Backfill excerpts for existing conflict events"""

import sys
import os
import json
from dataclasses import asdict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal
from app.models import Event, Article
from app.services.coherence import (
    generate_conflict_explanation,
    group_by_political_bias,
    has_political_diversity,
    identify_narrative_perspectives,
)
from app.services.embed import generate_embeddings
from loguru import logger


def backfill_conflict_excerpts(max_events: int = 50):
    """
    Backfill excerpts for existing conflict events that don't have them.
    
    Args:
        max_events: Maximum number of events to process
    """
    logger.info(f"🔄 Starting backfill of excerpts for conflict events...")
    
    with SessionLocal() as db:
        # Find all conflict events without excerpts
        conflicts = (
            db.query(Event)
            .filter(Event.has_conflict == True)
            .filter(Event.conflict_explanation_json != None)
            .order_by(Event.importance_score.desc())
            .limit(max_events)
            .all()
        )
        
        total_conflicts = len(conflicts)
        processed = 0
        already_had = 0
        
        logger.info(f"Found {total_conflicts} conflict events to check")
        
        for i, event in enumerate(conflicts):
            try:
                # Check if already has excerpts
                explanation = json.loads(event.conflict_explanation_json)
                if any(p.get("representative_excerpts") for p in explanation.get("perspectives", [])):
                    already_had += 1
                    continue
                
                # Get articles
                articles = db.query(Article).filter(Article.cluster_id == event.id).all()
                if not articles or len(articles) < 2:
                    continue
                
                # Generate embeddings
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
                processed += 1
                
                if (i + 1) % 10 == 0:
                    db.commit()
                    logger.info(f"Processed {i + 1}/{total_conflicts} events...")
                
            except Exception as e:
                logger.error(f"Failed to process event {event.id}: {e}")
                db.rollback()
                continue
        
        db.commit()
        
        logger.info(f"✅ Backfill complete:")
        logger.info(f"  - {total_conflicts} total conflicts checked")
        logger.info(f"  - {already_had} already had excerpts")
        logger.info(f"  - {processed} newly extracted")
        logger.info(f"  - {total_conflicts - already_had - processed} failed/skipped")


if __name__ == "__main__":
    backfill_conflict_excerpts()
