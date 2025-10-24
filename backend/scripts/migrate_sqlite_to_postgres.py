#!/usr/bin/env python3
"""
Migrate SQLite database to PostgreSQL

This script:
1. Reads all data from local SQLite database
2. Connects to remote PostgreSQL database
3. Inserts all events and articles

Usage:
    python backend/scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys
from pathlib import Path

import psycopg2
import sqlite3
from datetime import datetime

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def get_sqlite_connection():
    """Connect to local SQLite database"""
    db_path = Path(__file__).parent.parent.parent / "data" / "app.db"
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found at {db_path}")

    print(f"✓ Found SQLite database at {db_path}")
    return sqlite3.connect(db_path)

def get_postgres_connection():
    """Connect to remote PostgreSQL database"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Parse PostgreSQL connection string
    # Format: postgresql://username:password@host:port/database
    try:
        conn = psycopg2.connect(database_url)
        print(f"✓ Connected to PostgreSQL at {database_url.split('@')[1]}")
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to PostgreSQL: {e}")

def count_records(sqlite_conn):
    """Count records in SQLite"""
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    event_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM articles_raw")
    article_count = cursor.fetchone()[0]

    print(f"\n📊 Local SQLite Database:")
    print(f"   Events: {event_count}")
    print(f"   Articles: {article_count}")

    return event_count, article_count

def migrate_events(sqlite_conn, postgres_conn):
    """Migrate events from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    # Get all events from SQLite
    sqlite_cursor.execute("""
        SELECT
            id, summary, articles_count, unique_sources, geo_diversity,
            evidence_flag, official_match, truth_score, underreported,
            coherence_score, has_conflict, conflict_severity,
            conflict_explanation_json, bias_compass_json, category,
            category_confidence, conflict_detected_at, conflict_history_json,
            importance_score, first_seen, last_seen, languages_json,
            international_coverage_json, created_at
        FROM events
        ORDER BY id
    """)

    events = sqlite_cursor.fetchall()
    print(f"\n🔄 Migrating {len(events)} events...")

    # Insert events into PostgreSQL
    insert_query = """
        INSERT INTO events (
            id, summary, articles_count, unique_sources, geo_diversity,
            evidence_flag, official_match, truth_score, underreported,
            coherence_score, has_conflict, conflict_severity,
            conflict_explanation_json, bias_compass_json, category,
            category_confidence, conflict_detected_at, conflict_history_json,
            importance_score, first_seen, last_seen, languages_json,
            international_coverage_json, created_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (id) DO UPDATE SET
            summary = EXCLUDED.summary,
            articles_count = EXCLUDED.articles_count,
            unique_sources = EXCLUDED.unique_sources,
            geo_diversity = EXCLUDED.geo_diversity,
            evidence_flag = EXCLUDED.evidence_flag,
            official_match = EXCLUDED.official_match,
            truth_score = EXCLUDED.truth_score,
            underreported = EXCLUDED.underreported,
            coherence_score = EXCLUDED.coherence_score,
            has_conflict = EXCLUDED.has_conflict,
            conflict_severity = EXCLUDED.conflict_severity,
            conflict_explanation_json = EXCLUDED.conflict_explanation_json,
            bias_compass_json = EXCLUDED.bias_compass_json,
            category = EXCLUDED.category,
            category_confidence = EXCLUDED.category_confidence,
            conflict_detected_at = EXCLUDED.conflict_detected_at,
            conflict_history_json = EXCLUDED.conflict_history_json,
            importance_score = EXCLUDED.importance_score,
            first_seen = EXCLUDED.first_seen,
            last_seen = EXCLUDED.last_seen,
            languages_json = EXCLUDED.languages_json,
            international_coverage_json = EXCLUDED.international_coverage_json,
            created_at = EXCLUDED.created_at
    """

    for i, event in enumerate(events):
        try:
            postgres_cursor.execute(insert_query, event)
            if (i + 1) % 50 == 0:
                print(f"   ✓ Inserted {i + 1}/{len(events)} events")
        except Exception as e:
            print(f"   ✗ Error inserting event {event[0]}: {e}")
            postgres_conn.rollback()
            raise

    postgres_conn.commit()
    print(f"✓ Successfully migrated {len(events)} events")

def migrate_articles(sqlite_conn, postgres_conn):
    """Migrate articles from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    # Get all articles from SQLite
    sqlite_cursor.execute("""
        SELECT
            id, source, title, url, timestamp, language, summary,
            text_snippet, entities_json, cluster_id, fact_check_status,
            fact_check_flags_json, source_country, source_region, ingested_at
        FROM articles_raw
        ORDER BY id
    """)

    articles = sqlite_cursor.fetchall()
    print(f"\n🔄 Migrating {len(articles)} articles...")

    # Insert articles into PostgreSQL
    insert_query = """
        INSERT INTO articles_raw (
            id, source, title, url, timestamp, language, summary,
            text_snippet, entities_json, cluster_id, fact_check_status,
            fact_check_flags_json, source_country, source_region, ingested_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (id) DO UPDATE SET
            source = EXCLUDED.source,
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            timestamp = EXCLUDED.timestamp,
            language = EXCLUDED.language,
            summary = EXCLUDED.summary,
            text_snippet = EXCLUDED.text_snippet,
            entities_json = EXCLUDED.entities_json,
            cluster_id = EXCLUDED.cluster_id,
            fact_check_status = EXCLUDED.fact_check_status,
            fact_check_flags_json = EXCLUDED.fact_check_flags_json,
            source_country = EXCLUDED.source_country,
            source_region = EXCLUDED.source_region,
            ingested_at = EXCLUDED.ingested_at
    """

    for i, article in enumerate(articles):
        try:
            postgres_cursor.execute(insert_query, article)
            if (i + 1) % 500 == 0:
                print(f"   ✓ Inserted {i + 1}/{len(articles)} articles")
        except Exception as e:
            print(f"   ✗ Error inserting article {article[0]}: {e}")
            postgres_conn.rollback()
            raise

    postgres_conn.commit()
    print(f"✓ Successfully migrated {len(articles)} articles")

def verify_migration(sqlite_conn, postgres_conn):
    """Verify migration was successful"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    # Count SQLite records
    sqlite_cursor.execute("SELECT COUNT(*) FROM events")
    sqlite_events = sqlite_cursor.fetchone()[0]

    sqlite_cursor.execute("SELECT COUNT(*) FROM articles_raw")
    sqlite_articles = sqlite_cursor.fetchone()[0]

    # Count PostgreSQL records
    postgres_cursor.execute("SELECT COUNT(*) FROM events")
    postgres_events = postgres_cursor.fetchone()[0]

    postgres_cursor.execute("SELECT COUNT(*) FROM articles_raw")
    postgres_articles = postgres_cursor.fetchone()[0]

    print(f"\n✅ Migration Verification:")
    print(f"   Events:   {sqlite_events} → {postgres_events} ({'✓' if sqlite_events == postgres_events else '✗'})")
    print(f"   Articles: {sqlite_articles} → {postgres_articles} ({'✓' if sqlite_articles == postgres_articles else '✗'})")

    if sqlite_events == postgres_events and sqlite_articles == postgres_articles:
        print(f"\n🎉 Migration successful!")
        return True
    else:
        print(f"\n❌ Migration incomplete - record counts don't match")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLite → PostgreSQL Migration")
    print("=" * 60)

    try:
        # Connect to databases
        sqlite_conn = get_sqlite_connection()
        postgres_conn = get_postgres_connection()

        # Count records
        count_records(sqlite_conn)

        # Migrate data
        migrate_events(sqlite_conn, postgres_conn)
        migrate_articles(sqlite_conn, postgres_conn)

        # Verify
        if verify_migration(sqlite_conn, postgres_conn):
            print("\nYour production database is now populated! 🚀")
            print("Visit: https://truthboard.vercel.app")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1

    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()

if __name__ == "__main__":
    sys.exit(main())
