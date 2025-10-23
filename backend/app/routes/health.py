"""Health check endpoint"""

from datetime import datetime

from app.db import check_db_health, get_db
from app.models import Article, Event
from app.schemas import HealthResponse
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Check system health status.

    Returns:
        - status: "healthy" or "unhealthy"
        - database: "connected" or "disconnected"
        - worker_last_run: timestamp of last ingestion
        - total_events: count of events
        - total_articles: count of articles
    """
    status = "healthy"
    db_status = "connected" if check_db_health() else "disconnected"

    try:
        # Get total counts
        total_events = db.query(func.count(Event.id)).scalar() or 0
        total_articles = db.query(func.count(Article.id)).scalar() or 0

        # Get last ingestion time (most recent article)
        last_article = db.query(Article).order_by(Article.ingested_at.desc()).first()
        worker_last_run = last_article.ingested_at if last_article else None

        # BUGFIX: Ensure timezone-aware datetime for proper frontend parsing
        if worker_last_run:
            from datetime import timezone
            if worker_last_run.tzinfo is None:
                worker_last_run = worker_last_run.replace(tzinfo=timezone.utc)

        if db_status == "disconnected":
            status = "unhealthy"

    except Exception as e:
        print(f"Health check error: {e}")
        status = "unhealthy"
        db_status = "error"
        total_events = 0
        total_articles = 0
        worker_last_run = None

    return HealthResponse(
        status=status,
        database=db_status,
        worker_last_run=worker_last_run,
        total_events=total_events,
        total_articles=total_articles,
    )


@router.get("/health/live")
async def liveness():
    """
    Kubernetes/Docker liveness probe.
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """
    Kubernetes/Docker readiness probe.
    Returns 200 if the application is ready to serve traffic.
    Returns 503 if database is not accessible.
    """
    from fastapi import HTTPException

    if not check_db_health():
        raise HTTPException(status_code=503, detail="Database not ready")

    return {"status": "ready", "database": "connected"}


@router.post("/health/ingest")
async def trigger_ingestion(db: Session = Depends(get_db)):
    """
    Manually trigger data ingestion pipeline.
    This will fetch articles from all sources and populate the database.
    """
    try:
        from app.workers.scheduler import run_ingestion_pipeline
        
        # Run the ingestion pipeline
        run_ingestion_pipeline()
        
        # Get updated counts
        total_events = db.query(func.count(Event.id)).scalar() or 0
        total_articles = db.query(func.count(Article.id)).scalar() or 0
        
        return {
            "status": "success",
            "message": "Ingestion pipeline completed",
            "total_events": total_events,
            "total_articles": total_articles
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ingestion failed: {str(e)}"
        }
