"""Database connection and session management"""

import os
from typing import Generator

from app.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Create database engine (supports both SQLite and PostgreSQL)
is_sqlite = settings.database_url.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    """Run database migrations"""
    try:
        db = SessionLocal()
        
        # Detect database type
        is_postgres = 'postgresql' in settings.database_url.lower()
        
        if is_postgres:
            # PostgreSQL: Check columns using information_schema
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events'
            """))
            columns = [row[0] for row in result.fetchall()]
        else:
            # SQLite: Use PRAGMA
            result = db.execute(text("PRAGMA table_info(events)"))
            columns = [row[1] for row in result.fetchall()]
        
        # Add category column if it doesn't exist
        if 'category' not in columns:
            print("➕ Adding 'category' column...")
            db.execute(text("ALTER TABLE events ADD COLUMN category VARCHAR(50)"))
            db.commit()
            print("✓ Added 'category' column")
        
        # Add category_confidence column if it doesn't exist
        if 'category_confidence' not in columns:
            print("➕ Adding 'category_confidence' column...")
            if is_postgres:
                db.execute(text("ALTER TABLE events ADD COLUMN category_confidence DOUBLE PRECISION"))
            else:
                db.execute(text("ALTER TABLE events ADD COLUMN category_confidence FLOAT"))
            db.commit()
            print("✓ Added 'category_confidence' column")
        
        db.close()
        print("✅ Database migrations completed")
        
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        # Don't fail startup if migrations fail
        pass


def init_db() -> None:
    """Initialize database tables"""
    # For SQLite, ensure data directory exists
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Run migrations
    run_migrations()
    
    print(f"Database initialized: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")


def check_db_health() -> bool:
    """Check if database is accessible"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False
