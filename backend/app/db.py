"""Database connection and session management"""

import os
from typing import Generator

from app.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Create SQLite engine
database_url = f"sqlite:///{settings.db_path}"
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False,  # Set to True for SQL query logging
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


def init_db() -> None:
    """Initialize database tables"""
    # Ensure data directory exists
    db_dir = os.path.dirname(settings.db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {settings.db_path}")


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
