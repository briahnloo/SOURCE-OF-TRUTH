"""Run ingestion pipeline once (for manual execution)"""

from app.db import init_db
from app.workers.scheduler import run_ingestion_pipeline

if __name__ == "__main__":
    print("🚀 Running ingestion pipeline once...\n")
    init_db()
    run_ingestion_pipeline()
    print("\n✅ Done!")
