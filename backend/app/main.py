"""FastAPI application entry point"""

import os
import sys
from contextlib import asynccontextmanager

from app.config import settings
from app.db import check_db_health, init_db
from app.routes import events, feeds, health
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Optional scheduler import (only if enabled)
scheduler = None
if os.getenv("ENABLE_SCHEDULER", "").lower() == "true":
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from app.workers.scheduler import run_ingestion_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global scheduler
    
    # Startup
    print("Starting Truth Layer Backend...")
    db_info = settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url
    print(f"Database: {db_info}")
    print(f"Allowed origins: {settings.allowed_origins}")

    # Initialize database
    try:
        init_db()
        if check_db_health():
            print("✅ Database initialized and healthy")
        else:
            print("❌ Database health check failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Start background scheduler if enabled
    if os.getenv("ENABLE_SCHEDULER", "").lower() == "true":
        print("🔄 Starting background scheduler...")
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            run_ingestion_pipeline,
            trigger=IntervalTrigger(minutes=15),
            id="ingestion_pipeline",
            name="Ingestion Pipeline",
            replace_existing=True,
        )
        scheduler.start()
        print("✅ Background scheduler started (15-minute interval)")
        
        # Run once immediately in background
        scheduler.add_job(
            run_ingestion_pipeline,
            id="initial_run",
            name="Initial Pipeline Run",
        )

    yield

    # Shutdown
    print("Shutting down Truth Layer Backend...")
    if scheduler:
        print("Stopping scheduler...")
        scheduler.shutdown()
        print("✅ Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="Truth Layer API",
    description="Truth-scored news events verified via open data sources",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(feeds.router, prefix="/feeds", tags=["Feeds"])


# Root endpoint
@app.get("/")
async def root():
    """API root"""
    return {
        "name": "Truth Layer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
