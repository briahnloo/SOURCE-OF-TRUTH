"""FastAPI application entry point"""

import sys
from contextlib import asynccontextmanager

from app.config import settings
from app.db import check_db_health, init_db
from app.routes import events, feeds, health
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting Truth Layer Backend...")
    print(f"Database: {settings.db_path}")
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

    yield

    # Shutdown
    print("Shutting down Truth Layer Backend...")


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
