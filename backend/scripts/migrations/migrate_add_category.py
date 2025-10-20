"""
Migration script to add category fields to events table.
Run this once to update your database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Get the database path
db_path = Path(__file__).parent.parent / "data" / "app.db"

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    sys.exit(1)

print(f"🔄 Migrating database at {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in cursor.fetchall()]
    
    changes_made = False
    
    # Add category column if it doesn't exist
    if 'category' not in columns:
        print("➕ Adding 'category' column...")
        cursor.execute("ALTER TABLE events ADD COLUMN category VARCHAR(50)")
        changes_made = True
        print("✓ Added 'category' column")
    else:
        print("✓ 'category' column already exists")
    
    # Add category_confidence column if it doesn't exist
    if 'category_confidence' not in columns:
        print("➕ Adding 'category_confidence' column...")
        cursor.execute("ALTER TABLE events ADD COLUMN category_confidence FLOAT")
        changes_made = True
        print("✓ Added 'category_confidence' column")
    else:
        print("✓ 'category_confidence' column already exists")
    
    if changes_made:
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("📊 You may want to recategorize existing events by running the clustering service.")
    else:
        print("\n✅ Database schema is already up to date!")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

