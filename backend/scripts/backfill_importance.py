"""Backfill importance scores for existing events"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal
from app.models import Event
from app.services.importance import calculate_importance_score


def backfill_importance_scores():
    """Calculate importance scores for all existing events"""
    db = SessionLocal()
    
    try:
        events = db.query(Event).all()
        total_events = len(events)
        
        print(f"🔄 Processing {total_events} events...")
        
        for i, event in enumerate(events):
            # Calculate importance score
            event.importance_score = calculate_importance_score(event)
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{total_events} events...")
        
        # Commit all changes
        db.commit()
        
        print(f"✅ Updated importance scores for {total_events} events")
        
        # Show some examples
        print("\n📊 Sample importance scores:")
        sample_events = db.query(Event).order_by(Event.importance_score.desc()).limit(5).all()
        for event in sample_events:
            print(f"  {event.importance_score:.1f} - {event.summary[:60]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_importance_scores()
