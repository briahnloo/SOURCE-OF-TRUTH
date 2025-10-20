#!/usr/bin/env python3
"""
Backfill coherence scores for existing events.

This script recalculates narrative coherence for all events that don't have
a coherence_score yet. Useful after initial migration or for fixing issues.

Usage:
    python scripts/backfill_coherence.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Article, Event
from app.services.coherence import calculate_narrative_coherence
from app.services.embed import generate_embeddings


def backfill_coherence():
    """Recalculate coherence for all events without scores"""
    print("🔍 Backfilling coherence scores...")
    print(f"Database: {settings.database_url}\n")

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Get events without coherence scores
        events = db.query(Event).filter(Event.coherence_score == None).all()

        if not events:
            print("✅ No events need backfilling. All events have coherence scores.")
            return

        print(f"Found {len(events)} events without coherence scores\n")

        updated_count = 0
        skipped_count = 0

        for i, event in enumerate(events, 1):
            print(f"[{i}/{len(events)}] Processing event {event.id}: {event.summary[:60]}...")

            # Get articles for this event
            articles = db.query(Article).filter(Article.cluster_id == event.id).all()

            if len(articles) < 2:
                print(f"  ⏭️  Skipped (only {len(articles)} article)")
                event.coherence_score = 100.0
                event.has_conflict = False
                event.conflict_severity = "none"
                skipped_count += 1
                continue

            try:
                # Generate embeddings
                texts = [f"{a.title} {a.summary or ''}" for a in articles]
                embeddings = generate_embeddings(texts)

                # Calculate coherence (now returns 3 values)
                coherence, severity, explanation = calculate_narrative_coherence(
                    articles, embeddings
                )

                # Update event
                event.coherence_score = coherence
                event.has_conflict = severity != "none"
                event.conflict_severity = severity

                # Store conflict explanation if present
                if explanation:
                    import json
                    from dataclasses import asdict

                    event.conflict_explanation_json = json.dumps(asdict(explanation))

                print(
                    f"  ✅ Updated: coherence={coherence:.1f}, severity={severity}, articles={len(articles)}"
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
        print(f"Skipped: {skipped_count} events (single article)")
        print(f"Total: {len(events)} events processed")
        print("=" * 60)

        # Show statistics
        print("\n📊 Coherence distribution:")
        high_coherence = (
            db.query(Event).filter(Event.coherence_score >= 80).count()
        )
        medium_coherence = (
            db.query(Event)
            .filter(Event.coherence_score >= 60, Event.coherence_score < 80)
            .count()
        )
        low_coherence = (
            db.query(Event)
            .filter(Event.coherence_score >= 40, Event.coherence_score < 60)
            .count()
        )
        very_low = db.query(Event).filter(Event.coherence_score < 40).count()

        print(f"  High (80-100): {high_coherence} events")
        print(f"  Medium (60-79): {medium_coherence} events")
        print(f"  Low (40-59): {low_coherence} events")
        print(f"  Very Low (0-39): {very_low} events")

        conflicts = db.query(Event).filter(Event.has_conflict == True).count()
        print(f"\n⚠️  Total conflicts: {conflicts} events")

        avg_coherence = db.query(Event).filter(Event.coherence_score != None).all()
        if avg_coherence:
            avg = sum(e.coherence_score for e in avg_coherence) / len(avg_coherence)
            print(f"📈 Average coherence: {avg:.1f}")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_coherence()


