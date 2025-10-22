"""Reset underreported flags to False"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, text
from app.config import settings


def migrate():
    """Reset all underreported flags to False"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Set all underreported flags to False
        result = conn.execute(text("UPDATE events SET underreported = 0"))
        conn.commit()
        
        count = result.rowcount
        
    print(f"✅ Reset underreported flags for {count} events")
    print("Note: Column preserved for backwards compatibility")


if __name__ == "__main__":
    migrate()

