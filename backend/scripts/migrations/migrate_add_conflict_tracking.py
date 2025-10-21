#!/usr/bin/env python3
"""
Migration: Add conflict tracking fields to events table

Adds:
- conflict_detected_at: DateTime field for when conflict first emerged
- conflict_history_json: Text field for timeline of coherence changes
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal, engine
from sqlalchemy import text


def run_migration():
    """Add conflict tracking fields to events table"""
    
    db = SessionLocal()
    
    try:
        print("Starting migration: Add conflict tracking fields...")
        
        # Check if columns already exist
        result = db.execute(text("PRAGMA table_info(events)"))
        existing_columns = {row[1] for row in result}
        
        if "conflict_detected_at" in existing_columns:
            print("✓ conflict_detected_at column already exists, skipping...")
        else:
            print("Adding conflict_detected_at column...")
            db.execute(text("ALTER TABLE events ADD COLUMN conflict_detected_at DATETIME"))
            print("✓ Added conflict_detected_at column")
        
        if "conflict_history_json" in existing_columns:
            print("✓ conflict_history_json column already exists, skipping...")
        else:
            print("Adding conflict_history_json column...")
            db.execute(text("ALTER TABLE events ADD COLUMN conflict_history_json TEXT"))
            print("✓ Added conflict_history_json column")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()

