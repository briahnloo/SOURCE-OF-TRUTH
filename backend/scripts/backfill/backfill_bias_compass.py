#!/usr/bin/env python3
"""
Backfill bias compass scores for existing events.

This script calculates bias compass data for all events that don't have it yet.
Useful after initial migration or for fixing issues.

Usage:
    python scripts/backfill_bias_compass.py
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Article, Event
from app.services.bias import BiasAnalyzer


def backfill_bias_compass():
    """Calculate bias compass for all events without scores"""
    print("🧭 Backfilling bias compass data...")
    print(f"Database: {settings.database_url}\n")

    # Initialize database
    init_db()
    db = SessionLocal()
    bias_analyzer = BiasAnalyzer()

    try:
        # Get events without bias compass
        events = db.query(Event).filter(Event.bias_compass_json == None).all()

        if not events:
            print("✅ No events need backfilling. All events have bias compass data.")
            return

        print(f"Found {len(events)} events without bias compass data\n")

        updated_count = 0
        skipped_count = 0

        for i, event in enumerate(events, 1):
            print(f"[{i}/{len(events)}] Processing event {event.id}: {event.summary[:60]}...")

            # Get articles for this event
            articles = db.query(Article).filter(Article.cluster_id == event.id).all()

            if len(articles) == 0:
                print(f"  ⏭️  Skipped (no articles)")
                skipped_count += 1
                continue

            try:
                # Get article sources
                article_sources = [a.source for a in articles]

                # Calculate bias compass
                bias_score = bias_analyzer.calculate_event_bias(article_sources)

                # Update event
                event.bias_compass_json = json.dumps(asdict(bias_score))

                print(
                    f"  ✅ Updated: Western={bias_score.geographic['western']:.2f}, "
                    f"Political Center={bias_score.political['center']:.2f}"
                )
                updated_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

            # Commit every 10 events
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Committed batch ({i} events processed)\n")

        # Final commit
        db.commit()

        print("\n" + "=" * 60)
        print("✅ Backfill complete!")
        print(f"Updated: {updated_count} events")
        print(f"Skipped: {skipped_count} events (no articles)")
        print(f"Total: {len(events)} events processed")
        print("=" * 60)

        # Show statistics
        print("\n📊 Bias distribution summary:")

        all_events = (
            db.query(Event).filter(Event.bias_compass_json != None).all()
        )

        if all_events:
            avg_western = sum(
                json.loads(e.bias_compass_json)["geographic"]["western"]
                for e in all_events
            ) / len(all_events)
            avg_center = sum(
                json.loads(e.bias_compass_json)["political"]["center"]
                for e in all_events
            ) / len(all_events)
            avg_factual = sum(
                json.loads(e.bias_compass_json)["tone"]["factual"] for e in all_events
            ) / len(all_events)

            print(f"  Average Western coverage: {avg_western * 100:.1f}%")
            print(f"  Average Political Center: {avg_center * 100:.1f}%")
            print(f"  Average Factual tone: {avg_factual * 100:.1f}%")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_bias_compass()

