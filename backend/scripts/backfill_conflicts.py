"""
Backfill script to populate the database with test conflict data for the conflicts section.
This creates realistic political events with diverse source coverage.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal
from app.models import Article, Event


def create_test_event_data():
    """Create test events with diverse source coverage for conflicts section."""
    db = SessionLocal()

    try:
        # Check if we already have events
        existing_count = db.query(Event).count()
        print(f"📊 Current events in database: {existing_count}")

        if existing_count > 0:
            print("✅ Database already has events. Conflicts section should populate if they have 2+ sources.")

            # Check how many would appear in conflicts
            conflicts_count = db.query(Event).filter(
                Event.unique_sources >= 2
            ).filter(
                (Event.category.in_(['politics', 'international'])) | (Event.category == None)
            ).count()

            print(f"📍 Events with 2+ sources (politics/international): {conflicts_count}")

            if conflicts_count == 0:
                print("\n⚠️  No events with 2+ sources. This is why conflicts section is empty.")
                print("→ Check your ingestion pipeline or manually ingest data.")

            return

        print("\n🔄 No events found. Creating test data...")

        # Test Event 1: Gaza Coverage
        print("\n  Creating Gaza coverage event...")
        now = datetime.utcnow()

        gaza_articles = [
            ("foxnews.com", "Hamas Attack Devastates Israeli Communities", now - timedelta(hours=0)),
            ("cnn.com", "Israel Responds to Attack; Civilian Casualties Reported", now - timedelta(hours=1)),
            ("aljazeera.com", "Palestinian Resistance Operation Targets Military", now - timedelta(hours=2)),
            ("bbc.com", "Escalation in Gaza as Violence Intensifies", now - timedelta(hours=3)),
            ("npr.org", "Middle East Crisis as Conflict Spreads", now - timedelta(hours=4)),
        ]

        for source, title, pub_date in gaza_articles:
            article = Article(
                url=f"https://{source}/article-gaza-1",
                source=source,
                title=title,
                content=f"Article about Gaza conflict from {source}",
                summary=title,
                published_at=pub_date,
                ingested_at=now,
                authors=[],
                images=[],
                key_entities=[],
            )
            db.add(article)

        db.flush()

        # Get the articles we just added
        gaza_article_ids = [a.id for a in db.query(Article).filter(
            Article.source.in_([s[0] for s in gaza_articles])
        ).all()]

        # Create event
        event1 = Event(
            summary="Gaza-Israel Conflict Escalates with New Violence",
            articles_count=len(gaza_articles),
            unique_sources=len(gaza_articles),
            geo_diversity=0.8,
            evidence_flag=False,
            official_match=False,
            truth_score=65.0,
            confidence_tier="developing",
            underreported=False,
            coherence_score=72.5,  # Moderate coherence - different framing
            has_conflict=True,
            conflict_severity="medium",
            conflict_explanation_json=None,
            bias_compass_json='{"left": 0.3, "center": 0.4, "right": 0.3}',
            category="international",
            category_confidence=0.95,
            importance_score=85.0,
            first_seen=now,
            last_seen=now,
            languages_json='["en"]',
        )
        db.add(event1)
        db.flush()

        # Link articles to event
        for article in db.query(Article).filter(Article.source.in_([s[0] for s in gaza_articles])).all():
            article.cluster_id = event1.id

        print(f"    ✓ Created Gaza event (ID: {event1.id}) with {len(gaza_articles)} sources")

        # Test Event 2: Trump Legal Case
        print("  Creating Trump legal case event...")

        trump_articles = [
            ("foxnews.com", "Trump Faces Politically Motivated Charges", now - timedelta(hours=5)),
            ("cnn.com", "Trump Indicted on Multiple Charges in Historic Case", now - timedelta(hours=6)),
            ("nytimes.com", "Former President Charged in Federal Indictment", now - timedelta(hours=7)),
            ("washingtonpost.com", "Trump Faces Serious Legal Jeopardy", now - timedelta(hours=8)),
            ("theguardian.com", "Trump Charges Represent Unprecedented Legal Moment", now - timedelta(hours=9)),
        ]

        for source, title, pub_date in trump_articles:
            article = Article(
                url=f"https://{source}/article-trump-1",
                source=source,
                title=title,
                content=f"Article about Trump from {source}",
                summary=title,
                published_at=pub_date,
                ingested_at=now,
                authors=[],
                images=[],
                key_entities=[],
            )
            db.add(article)

        db.flush()

        event2 = Event(
            summary="Trump Faces Indictment",
            articles_count=len(trump_articles),
            unique_sources=len(trump_articles),
            geo_diversity=0.2,
            evidence_flag=False,
            official_match=True,
            truth_score=78.0,
            confidence_tier="confirmed",
            underreported=False,
            coherence_score=68.0,  # Different framing
            has_conflict=True,
            conflict_severity="medium",
            conflict_explanation_json=None,
            bias_compass_json='{"left": 0.5, "center": 0.3, "right": 0.2}',
            category="politics",
            category_confidence=0.98,
            importance_score=92.0,
            first_seen=now,
            last_seen=now,
            languages_json='["en"]',
        )
        db.add(event2)
        db.flush()

        for article in db.query(Article).filter(Article.source.in_([s[0] for s in trump_articles])).all():
            article.cluster_id = event2.id

        print(f"    ✓ Created Trump event (ID: {event2.id}) with {len(trump_articles)} sources")

        # Test Event 3: Border/Immigration
        print("  Creating border/immigration event...")

        border_articles = [
            ("foxnews.com", "Border Crisis: Surge of Illegal Crossings", now - timedelta(hours=10)),
            ("cnn.com", "Biden Administration Addresses Border Challenges", now - timedelta(hours=11)),
            ("bbc.com", "US Border Experiences Record Crossings", now - timedelta(hours=12)),
            ("apnews.com", "Border Crossings Reach New Levels", now - timedelta(hours=13)),
            ("politico.com", "Immigration Becomes Central Political Issue", now - timedelta(hours=14)),
        ]

        for source, title, pub_date in border_articles:
            article = Article(
                url=f"https://{source}/article-border-1",
                source=source,
                title=title,
                content=f"Article about border from {source}",
                summary=title,
                published_at=pub_date,
                ingested_at=now,
                authors=[],
                images=[],
                key_entities=[],
            )
            db.add(article)

        db.flush()

        event3 = Event(
            summary="Border Crossing Numbers Reach New Levels",
            articles_count=len(border_articles),
            unique_sources=len(border_articles),
            geo_diversity=0.6,
            evidence_flag=False,
            official_match=True,
            truth_score=72.0,
            confidence_tier="developing",
            underreported=False,
            coherence_score=75.0,  # Similar facts, different emphasis
            has_conflict=True,
            conflict_severity="low",
            conflict_explanation_json=None,
            bias_compass_json='{"left": 0.3, "center": 0.4, "right": 0.3}',
            category="politics",
            category_confidence=0.92,
            importance_score=78.0,
            first_seen=now,
            last_seen=now,
            languages_json='["en"]',
        )
        db.add(event3)
        db.flush()

        for article in db.query(Article).filter(Article.source.in_([s[0] for s in border_articles])).all():
            article.cluster_id = event3.id

        print(f"    ✓ Created border event (ID: {event3.id}) with {len(border_articles)} sources")

        # Commit all changes
        db.commit()

        print(f"\n✅ Created 3 test conflict events with diverse source coverage!")

        # Verify
        total = db.query(Event).count()
        conflicts = db.query(Event).filter(
            Event.unique_sources >= 2
        ).filter(
            (Event.category.in_(['politics', 'international'])) | (Event.category == None)
        ).count()

        print(f"\n📊 Database summary:")
        print(f"   Total events: {total}")
        print(f"   Events with 2+ sources (politics/international): {conflicts}")
        print(f"\n✨ These {conflicts} events should now appear in the conflicts section!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Backfilling test conflict data for conflicts section...\n")
    create_test_event_data()
    print("\n💡 Restart your backend and hard refresh to see the conflicts section populate.")
