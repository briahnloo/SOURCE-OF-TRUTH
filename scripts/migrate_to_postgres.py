#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL

Usage:
    python scripts/migrate_to_postgres.py

Environment variables required:
    SOURCE_DB=sqlite:////data/app.db
    TARGET_DB=postgresql://user:pass@host:5432/dbname
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

def migrate():
    """Migrate all data from SQLite to PostgreSQL"""
    
    source_url = os.getenv("SOURCE_DB", "sqlite:////data/app.db")
    target_url = os.getenv("TARGET_DB")
    
    if not target_url:
        print("❌ Error: TARGET_DB environment variable not set")
        print("Example: export TARGET_DB=postgresql://user:pass@host:5432/dbname")
        sys.exit(1)
    
    print(f"Migrating from SQLite to PostgreSQL...")
    print(f"Source: {source_url}")
    print(f"Target: {target_url.split('@')[0]}@***")  # Hide password
    
    # Create engines
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)
    
    # Reflect source schema
    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine)
    
    # Create target schema
    print("\n📊 Creating tables in PostgreSQL...")
    source_metadata.create_all(target_engine)
    
    # Create sessions
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    try:
        # Migrate each table
        for table_name in source_metadata.tables.keys():
            table = Table(table_name, source_metadata, autoload_with=source_engine)
            
            print(f"\n📦 Migrating table: {table_name}")
            
            # Read from source
            source_data = source_session.execute(table.select()).fetchall()
            
            if not source_data:
                print(f"   ℹ️  No data in {table_name}")
                continue
            
            # Insert into target
            for row in source_data:
                row_dict = dict(row._mapping)
                insert_stmt = table.insert().values(**row_dict)
                target_session.execute(insert_stmt)
            
            target_session.commit()
            print(f"   ✅ Migrated {len(source_data)} rows")
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update .env with new DATABASE_URL")
        print("2. Restart backend and worker: docker-compose restart backend worker")
        print("3. Verify: curl http://localhost:8000/health")
        
    except Exception as e:
        target_session.rollback()
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    migrate()

