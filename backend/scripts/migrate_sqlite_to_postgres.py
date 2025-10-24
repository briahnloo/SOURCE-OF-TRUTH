#!/usr/bin/env python3
"""
Migration script to transfer data from local SQLite to PostgreSQL on Render.

This script:
1. Connects to local SQLite database
2. Connects to PostgreSQL database on Render
3. Transfers all events and articles data
4. Handles duplicates with ON CONFLICT logic
5. Verifies the migration was successful

Usage:
    export DATABASE_URL="postgresql://username:password@host.onrender.com:5432/dbname"
    python backend/scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Event, Article
from app.db import Base

def get_sqlite_engine():
    """Get SQLite engine for local database"""
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'app.db')
    sqlite_url = f"sqlite:///{sqlite_path}"
    return create_engine(sqlite_url, echo=False)

def get_postgres_engine():
    """Get PostgreSQL engine for Render database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    if not database_url.startswith('postgresql://'):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
    
    return create_engine(database_url, echo=False)

def get_table_data(session, model_class, table_name: str) -> List[Dict[str, Any]]:
    """Get all data from a table as dictionaries"""
    print(f"📖 Reading {table_name} from local database...")
    
    # Get all records
    records = session.query(model_class).all()
    
    # Convert to dictionaries
    data = []
    for record in records:
        record_dict = {}
        for column in model_class.__table__.columns:
            value = getattr(record, column.name)
            # Handle datetime objects
            if isinstance(value, datetime):
                value = value.isoformat()
            record_dict[column.name] = value
        data.append(record_dict)
    
    print(f"✓ Found {len(data)} records in {table_name}")
    return data

def insert_events(postgres_session, events_data: List[Dict[str, Any]]) -> None:
    """Insert events data into PostgreSQL"""
    print(f"📝 Inserting {len(events_data)} events into PostgreSQL...")
    
    for i, event_data in enumerate(events_data):
        try:
            # Handle JSON fields that might be None
            for json_field in ['conflict_explanation_json', 'bias_compass_json', 
                             'conflict_history_json', 'languages_json', 'international_coverage_json']:
                if event_data.get(json_field) is None:
                    event_data[json_field] = None
            
            # Convert datetime strings back to datetime objects
            for date_field in ['first_seen', 'last_seen', 'conflict_detected_at', 'created_at']:
                if event_data.get(date_field):
                    event_data[date_field] = datetime.fromisoformat(event_data[date_field])
            
            # Insert with ON CONFLICT handling
            insert_sql = """
                INSERT INTO events (
                    id, summary, articles_count, unique_sources, geo_diversity,
                    evidence_flag, official_match, truth_score, underreported,
                    coherence_score, has_conflict, conflict_severity,
                    conflict_explanation_json, bias_compass_json, category,
                    category_confidence, conflict_detected_at, conflict_history_json,
                    importance_score, first_seen, last_seen, languages_json,
                    international_coverage_json, created_at
                ) VALUES (
                    :id, :summary, :articles_count, :unique_sources, :geo_diversity,
                    :evidence_flag, :official_match, :truth_score, :underreported,
                    :coherence_score, :has_conflict, :conflict_severity,
                    :conflict_explanation_json, :bias_compass_json, :category,
                    :category_confidence, :conflict_detected_at, :conflict_history_json,
                    :importance_score, :first_seen, :last_seen, :languages_json,
                    :international_coverage_json, :created_at
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
            
            postgres_session.execute(text(insert_sql), event_data)
            
            if (i + 1) % 50 == 0:
                print(f"  📝 Processed {i + 1}/{len(events_data)} events...")
                
        except Exception as e:
            print(f"⚠️ Error inserting event {event_data.get('id', 'unknown')}: {e}")
            continue
    
    postgres_session.commit()
    print(f"✓ Successfully inserted/updated {len(events_data)} events")

def insert_articles(postgres_session, articles_data: List[Dict[str, Any]]) -> None:
    """Insert articles data into PostgreSQL"""
    print(f"📝 Inserting {len(articles_data)} articles into PostgreSQL...")
    
    batch_size = 50  # Process in smaller batches
    successful_inserts = 0
    
    for i in range(0, len(articles_data), batch_size):
        batch = articles_data[i:i + batch_size]
        
        try:
            # Start a new transaction for each batch
            postgres_session.rollback()  # Clear any previous transaction errors
            
            for article_data in batch:
                # Convert datetime strings back to datetime objects
                for date_field in ['timestamp', 'ingested_at']:
                    if article_data.get(date_field):
                        article_data[date_field] = datetime.fromisoformat(article_data[date_field])
                
                # Insert with ON CONFLICT handling
                insert_sql = """
                    INSERT INTO articles_raw (
                        id, source, title, url, timestamp, language, summary,
                        text_snippet, entities_json, cluster_id, fact_check_status,
                        fact_check_flags_json, source_country, source_region, ingested_at
                    ) VALUES (
                        :id, :source, :title, :url, :timestamp, :language, :summary,
                        :text_snippet, :entities_json, :cluster_id, :fact_check_status,
                        :fact_check_flags_json, :source_country, :source_region, :ingested_at
                    )
                    ON CONFLICT (url) DO UPDATE SET
                        source = EXCLUDED.source,
                        title = EXCLUDED.title,
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
                
                postgres_session.execute(text(insert_sql), article_data)
            
            # Commit the batch
            postgres_session.commit()
            successful_inserts += len(batch)
            
            if (i + batch_size) % 500 == 0:
                print(f"  📝 Processed {i + batch_size}/{len(articles_data)} articles...")
                
        except Exception as e:
            print(f"⚠️ Error inserting batch {i//batch_size + 1}: {e}")
            postgres_session.rollback()  # Rollback the failed batch
            continue
    
    print(f"✓ Successfully inserted/updated {successful_inserts} articles")

def verify_migration(postgres_session) -> None:
    """Verify the migration was successful"""
    print("🔍 Verifying migration...")
    
    # Check events count
    events_count = postgres_session.execute(text("SELECT COUNT(*) FROM events")).scalar()
    print(f"✓ Events in PostgreSQL: {events_count}")
    
    # Check articles count
    articles_count = postgres_session.execute(text("SELECT COUNT(*) FROM articles_raw")).scalar()
    print(f"✓ Articles in PostgreSQL: {articles_count}")
    
    # Check for data integrity
    events_with_articles = postgres_session.execute(text("""
        SELECT COUNT(DISTINCT e.id) 
        FROM events e 
        JOIN articles_raw a ON e.id = a.cluster_id
    """)).scalar()
    print(f"✓ Events with articles: {events_with_articles}")
    
    # Check truth scores
    avg_truth_score = postgres_session.execute(text("""
        SELECT AVG(truth_score) FROM events WHERE truth_score IS NOT NULL
    """)).scalar()
    print(f"✓ Average truth score: {avg_truth_score:.2f}")
    
    print("🎉 Migration verification complete!")

def main():
    """Main migration function"""
    print("🚀 Starting SQLite to PostgreSQL migration...")
    print("=" * 60)
    
    try:
        # Connect to local SQLite database
        print("📱 Connecting to local SQLite database...")
        sqlite_engine = get_sqlite_engine()
        sqlite_session = sessionmaker(bind=sqlite_engine)()
        
        # Connect to PostgreSQL database
        print("☁️ Connecting to PostgreSQL database on Render...")
        postgres_engine = get_postgres_engine()
        postgres_session = sessionmaker(bind=postgres_engine)()
        
        # Create tables in PostgreSQL if they don't exist
        print("🏗️ Ensuring PostgreSQL tables exist...")
        Base.metadata.create_all(bind=postgres_engine)
        
        # Get data from SQLite
        print("\n📖 Reading data from local SQLite database...")
        events_data = get_table_data(sqlite_session, Event, "events")
        articles_data = get_table_data(sqlite_session, Article, "articles_raw")
        
        # Insert data into PostgreSQL
        print("\n📝 Transferring data to PostgreSQL...")
        if events_data:
            insert_events(postgres_session, events_data)
        
        if articles_data:
            insert_articles(postgres_session, articles_data)
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        verify_migration(postgres_session)
        
        print("\n" + "=" * 60)
        print("🎉 Migration successful!")
        print(f"✅ Transferred {len(events_data)} events and {len(articles_data)} articles")
        print("🌐 Your data is now live at: https://truthboard.vercel.app")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("💡 Make sure your DATABASE_URL is correct and accessible")
        sys.exit(1)
    
    finally:
        # Clean up connections
        try:
            sqlite_session.close()
            postgres_session.close()
        except:
            pass

if __name__ == "__main__":
    main()