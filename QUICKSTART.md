# Truth Layer MVP - Quick Start Guide

Welcome to the Truth Layer MVP! This guide will help you get the entire system running locally in under 5 minutes.

## Prerequisites

- **Docker** 20.10+ and **docker-compose** 1.29+
- 4GB free RAM
- 10GB free disk space
- Internet connection for data fetching

## Step 1: Initial Setup

```bash
# Navigate to project directory
cd "SINGLE SOURCE OF TRUTH"

# Create environment file
cp .env.example .env

# (Optional) Add API keys to .env
# nano .env
# Add your NEWSAPI_KEY, MEDIASTACK_KEY if you have them
```

## Step 2: Start the System

```bash
# Build and start all services
make dev
```

This will:
1. Build Docker images for backend, worker, and frontend
2. Download ML models (sentence-transformers, spaCy)
3. Initialize SQLite database
4. Start all services
5. Run initial data ingestion

**Expected startup time: 2-3 minutes**

## Step 3: Access the Application

Once services are running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **RSS Feed**: http://localhost:8000/feeds/verified.xml

## Step 4: Wait for Data

The worker runs ingestion every 15 minutes. Initial data will appear after the first cycle completes (3-5 minutes).

You can monitor progress:

```bash
# Watch logs
make logs

# Or specific service
docker-compose logs -f worker
```

## What to Expect

After the first ingestion cycle, you should see:

- **Confirmed Events**: High-confidence stories (≥75 score)
- **Developing Events**: Moderate coverage (40-74 score)
- **Underreported**: Stories from NGO/Gov sources missing from major wires
- **Stats**: Aggregate metrics and top sources

## Common Commands

```bash
# Stop services
make down

# View logs
make logs

# Run single ingestion manually
make ingest-once

# Run tests
make test

# Clean everything (delete database)
make clean

# Help
make help
```

## Troubleshooting

### Services won't start

```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000

# If blocked, stop conflicting services or change ports in docker-compose.yml
```

### No data appearing

```bash
# Check worker logs
docker-compose logs worker

# Manually trigger ingestion
make ingest-once

# Common issue: Rate limits on external APIs
# Solution: Wait 15 minutes or add API keys to .env
```

### Frontend shows API error

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Restart if needed
make down && make dev
```

### Database errors

```bash
# Reset database
make clean
make dev
```

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend    │────▶│    Worker    │
│  (Next.js)  │     │  (FastAPI)   │     │ (Scheduler)  │
│   :3000     │     │    :8000     │     │  (15 min)    │
└─────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                    ┌────────────────────────────────┐
                    │      SQLite Database           │
                    │       /data/app.db             │
                    └────────────────────────────────┘
```

## Data Sources

The system ingests from:

- **GDELT**: Global news mentions (15-min updates)
- **RSS Feeds**: 20+ outlets (AP, Reuters, BBC, etc.)
- **Reddit**: r/worldnews, r/news
- **NewsAPI**: Optional (requires free key)
- **Mediastack**: Optional (requires free key)
- **NGO/Gov**: ReliefWeb, USGS, WHO, UN OCHA

## How It Works

1. **Ingest** (every 15 min): Fetch articles from all sources
2. **Normalize**: Deduplicate, extract entities, detect language
3. **Embed**: Generate sentence embeddings
4. **Cluster**: Group related articles into events
5. **Score**: Calculate truth confidence (0-100)
6. **Tag**: Detect underreported stories
7. **Serve**: Expose via API and RSS feed

## Scoring Algorithm

Truth confidence is calculated as:

```
score = (sources × 0.25) + (geo_diversity × 0.40) +
        (evidence × 0.20) + (official_match × 0.15)
```

**Tiers:**
- **Confirmed** (≥75): High trust, multiple independent sources
- **Developing** (40-74): Moderate coverage, verification in progress
- **Unverified** (<40): Hidden from UI

See `/docs/scoring.md` for detailed breakdown.

## Next Steps

- **Explore the UI**: Visit http://localhost:3000 and browse events
- **Check API**: Visit http://localhost:8000/docs for interactive docs
- **Read Documentation**: See `/docs/` for architecture, API reference, etc.
- **Add Sources**: Edit `backend/app/services/fetch/rss.py` to add feeds
- **Customize Scoring**: Adjust weights in `backend/app/config.py`
- **Monitor**: Set up Discord webhook in `.env` for alerts

## Production Deployment

For production use:

1. Replace SQLite with PostgreSQL
2. Add Redis for API caching
3. Enable HTTPS with nginx reverse proxy
4. Set up monitoring (Prometheus/Grafana)
5. Configure rate limiting
6. Review and adjust retention policies

See `/docs/runbook.md` for operational details.

## Getting Help

- **Documentation**: `/docs/` directory
- **Issues**: Open a GitHub issue
- **Logs**: `make logs` for debugging
- **Health**: http://localhost:8000/health

## License

MIT - See LICENSE file

---

**Congratulations! Your Truth Layer MVP is now running locally.** 🎉

Visit http://localhost:3000 to start exploring truth-scored news events.
