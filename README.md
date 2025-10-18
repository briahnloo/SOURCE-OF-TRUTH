# The Truthboard - Truth Layer MVP

A single site showing what's actually true right now — verified via open data — plus a safe way to surface credible stories traditional media ignores.

## Features

- **Automated Ingestion**: Pulls from GDELT, RSS feeds, Reddit, NGO/Gov sources (USGS, WHO, NASA, UN)
- **Truth Confidence Scoring**: Weighted algorithm based on source diversity, evidence, and official data matching
- **Event Clustering**: Groups related articles using embeddings and DBSCAN
- **Underreported Detection**: Surfaces stories missing from major outlets
- **Clean Dashboard**: Next.js UI with confidence meters and evidence drawers
- **RSS Feed**: Subscribe to verified events at `/feeds/verified.xml`

## Quick Start

```bash
# 1. Clone and enter directory
cd "SINGLE SOURCE OF TRUTH"

# 2. Copy environment template
cp .env.example .env

# 3. (Optional) Add API keys to .env
# NEWSAPI_KEY=your_key_here
# MEDIASTACK_KEY=your_key_here

# 4. Start the stack
make dev

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Health Check: http://localhost:8000/health
```

## Architecture

**Stack:**
- Backend: FastAPI + SQLAlchemy + SQLite
- Worker: APScheduler (15-min ingestion cycles)
- Frontend: Next.js 14 + Tailwind CSS
- ML: sentence-transformers (local embeddings)

**Data Flow:**
```
[Free Sources] → Ingest → Normalize → Embed → Cluster → Score → Tag → RSS
                                                            ↓
                                                [SQLite] ← API → [UI]
```

## Commands

```bash
make dev          # Build and start all services
make down         # Stop all services
make logs         # Tail logs
make ingest-once  # Run single pipeline manually
make embed-cache  # Pre-download ML model
make test         # Run all tests
make clean        # Clean up database and volumes
```

## Documentation

- [Architecture Details](docs/architecture.md)
- [API Reference](docs/api.md)
- [Scoring Algorithm](docs/scoring.md)
- [Data Sources](docs/sources.md)
- [Operations Runbook](docs/runbook.md)

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **NLP**: sentence-transformers, spaCy, scikit-learn
- **Worker**: APScheduler, feedparser, requests
- **Frontend**: Next.js 14, React 18, Tailwind CSS, TypeScript
- **Infra**: Docker, docker-compose

## License

MIT License - See LICENSE file for details

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
