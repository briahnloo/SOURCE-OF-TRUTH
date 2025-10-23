"""Migration to add international source tracking columns"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine, text
from app.config import settings


def run_migration():
    """Add international tracking columns to database"""
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Add columns to articles_raw table
            print("Adding source_country and source_region to articles_raw table...")
            conn.execute(text("""
                ALTER TABLE articles_raw 
                ADD COLUMN source_country VARCHAR(10),
                ADD COLUMN source_region VARCHAR(20)
            """))
            
            # Add index for source_country
            print("Adding index for source_country...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_articles_source_country 
                ON articles_raw(source_country)
            """))
            
            # Add international_coverage_json to events table
            print("Adding international_coverage_json to events table...")
            conn.execute(text("""
                ALTER TABLE events 
                ADD COLUMN international_coverage_json TEXT
            """))
            
            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    run_migration()