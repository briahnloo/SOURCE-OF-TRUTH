"""Add importance_score column to events table"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, text
from app.config import settings


def migrate():
    """Add importance_score column and index to events table"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Add the column with default value
        conn.execute(text("ALTER TABLE events ADD COLUMN importance_score REAL DEFAULT 0.0"))
        
        # Create index for performance
        conn.execute(text("CREATE INDEX idx_events_importance ON events(importance_score)"))
        
        # Commit the transaction
        conn.commit()
        
    print("✅ Added importance_score column and index to events table")


if __name__ == "__main__":
    migrate()
