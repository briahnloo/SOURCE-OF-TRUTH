"""
Backfill detailed LLM explanations for existing conflict events.
Run: python -m backend.scripts.backfill.backfill_conflict_explanations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.db import SessionLocal
from app.models import Event, Article
from app.services.coherence import generate_detailed_conflict_explanation, NarrativePerspective
import json


def backfill_explanations(limit=None):
    """
    Backfill LLM-generated explanations for existing conflict events.
    
    Args:
        limit: Maximum number of events to process (None for all)
    """
    db = SessionLocal()
    try:
        # Find events with conflicts that have generic explanations
        events = db.query(Event).filter(
            Event.has_conflict == True,
            Event.conflict_explanation_json.isnot(None)
        ).all()
        
        if limit:
            events = events[:limit]
        
        print(f"Found {len(events)} conflict events to process")
        
        updated = 0
        skipped = 0
        failed = 0
        
        for event in events:
            try:
                explanation = json.loads(event.conflict_explanation_json)
                
                # Check if explanation is generic (heuristic)
                key_diff = explanation.get('key_difference', '')
                if any(generic in key_diff for generic in [
                    'emotional tones', 'key facts and entities', 
                    'emphasize certain aspects', 'different interpretations'
                ]):
                    # Rebuild perspectives
                    perspectives_data = explanation.get('perspectives', [])
                    if len(perspectives_data) >= 2:
                        # Get articles for this event (may be empty if deleted due to 30-day retention)
                        articles = db.query(Article).filter(
                            Article.cluster_id == event.id
                        ).all()
                        
                        # Generate new explanation (works even without articles)
                        perspective_objects = [
                            NarrativePerspective(**p) for p in perspectives_data
                        ]
                        
                        # Use event summary/title even if articles are gone
                        event_summary = event.summary or event.title or "Unknown event"
                        
                        new_explanation = generate_detailed_conflict_explanation(
                            perspective_objects,
                            event_summary,
                            articles  # Can be empty list
                        )
                        
                        if new_explanation:
                            explanation['key_difference'] = new_explanation
                            event.conflict_explanation_json = json.dumps(explanation)
                            updated += 1
                            print(f"✓ Updated event {event.id}: {(event.summary or event.title)[:60]}...")
                        else:
                            print(f"⊘ Skipped event {event.id}: LLM generation returned None")
                            skipped += 1
                    else:
                        print(f"⊘ Skipped event {event.id}: Not enough perspectives")
                        skipped += 1
                else:
                    print(f"⊘ Skipped event {event.id}: Already has specific explanation")
                    skipped += 1
                        
            except Exception as e:
                print(f"✗ Failed to update event {event.id}: {e}")
                failed += 1
                continue
        
        db.commit()
        print(f"\n✅ Backfill complete:")
        print(f"   • Updated: {updated}/{len(events)} events")
        print(f"   • Skipped: {skipped} events")
        print(f"   • Failed: {failed} events")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill LLM explanations for conflict events')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of events to process (default: 50)')
    parser.add_argument('--all', action='store_true', help='Process all events (overrides --limit)')
    
    args = parser.parse_args()
    
    limit = None if args.all else args.limit
    
    print(f"Starting backfill with limit={'all' if limit is None else limit}...")
    backfill_explanations(limit=limit)

