# Operations Runbook

This guide covers how to deploy, monitor, troubleshoot, and maintain the Truth Layer MVP.

## Quick Start

### Prerequisites

- Docker 20.10+
- docker-compose 1.29+
- 4GB free RAM
- 10GB free disk space

### First-Time Setup

```bash
# 1. Navigate to project directory
cd "SINGLE SOURCE OF TRUTH"

# 2. Create environment file
cp .env.example .env

# 3. (Optional) Add API keys for NewsAPI/Mediastack
nano .env

# 4. Start the stack
make dev

# 5. Wait for services to initialize (~2 minutes)
# Backend will be at http://localhost:8000
# Frontend will be at http://localhost:3000

# 6. Verify health
curl http://localhost:8000/health
```

### Stopping the System

```bash
# Stop all services (keeps data)
make down

# Stop and remove database (clean slate)
make clean
```

## Architecture Overview

```
┌─────────────────┐
│   Frontend      │  :3000 (Next.js)
│   Container     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   Backend       │  :8000 (FastAPI)
│   Container     │
└────────┬────────┘
         │ SQLite
         ▼
┌─────────────────┐       ┌─────────────────┐
│   Worker        │       │   /data volume  │
│   Container     │◄──────┤   app.db        │
└─────────────────┘       └─────────────────┘
```

## Monitoring

### Health Checks

**Backend Health:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "worker_last_run": "2025-10-18T14:30:00Z",
  "total_events": 42,
  "total_articles": 156
}
```

**Frontend Health:**
- Visit http://localhost:3000
- Check for green status indicator in top-right corner

### Log Monitoring

**Tail all services:**
```bash
make logs
```

**Individual service logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend
```

**Search logs for errors:**
```bash
docker-compose logs | grep ERROR
docker-compose logs | grep CRITICAL
```

### Key Metrics

**Ingestion Pipeline:**
- Expected cycle time: 3-5 minutes every 15 minutes
- Articles per cycle: 200-500 (varies by news activity)
- Events created per cycle: 10-50

**Database Growth:**
- Expected size: ~10-20MB per day
- Max size (30-day retention): ~500MB

**API Response Times:**
- `/health`: <50ms
- `/events`: <200ms
- `/events/{id}`: <100ms
- `/feeds/verified.xml`: <500ms

## Common Operations

### Manual Ingestion Run

Trigger ingestion outside of 15-min schedule:

```bash
make ingest-once
```

Or via docker-compose:
```bash
docker-compose exec worker python -m app.workers.run_once
```

### Pre-Download ML Model

To speed up first ingestion, cache the sentence-transformers model:

```bash
make embed-cache
```

This downloads ~80MB to `~/.cache/torch/sentence_transformers/`.

### Database Inspection

**Enter SQLite shell:**
```bash
docker-compose exec backend sqlite3 /data/app.db
```

**Useful queries:**
```sql
-- Count articles
SELECT COUNT(*) FROM articles_raw;

-- Count events by tier
SELECT
  CASE
    WHEN truth_score >= 75 THEN 'confirmed'
    WHEN truth_score >= 40 THEN 'developing'
    ELSE 'unverified'
  END AS tier,
  COUNT(*)
FROM events
GROUP BY tier;

-- Top sources
SELECT source, COUNT(*) as count
FROM articles_raw
GROUP BY source
ORDER BY count DESC
LIMIT 10;

-- Recent events
SELECT id, summary, truth_score, articles_count
FROM events
ORDER BY created_at DESC
LIMIT 5;
```

### Database Backup

```bash
# Create backup
docker-compose exec backend sqlite3 /data/app.db ".backup /data/backup_$(date +%Y%m%d).db"

# Copy to host
docker cp truth-layer-backend:/data/backup_20251018.db ./backups/
```

### Database Restore

```bash
# Copy backup to container
docker cp ./backups/backup_20251018.db truth-layer-backend:/data/restore.db

# Replace current DB (while services stopped)
make down
cp ./data/restore.db ./data/app.db
make dev
```

### Reset Database

```bash
# Warning: This deletes all data
make clean
make dev
```

## Troubleshooting

### Issue: Services won't start

**Symptoms:**
- `docker-compose up` exits with error
- Port conflicts

**Diagnosis:**
```bash
# Check if ports 3000 or 8000 are in use
lsof -i :3000
lsof -i :8000

# Check Docker status
docker ps -a
```

**Resolution:**
```bash
# Stop conflicting services
kill <PID_FROM_LSOF>

# Or change ports in docker-compose.yml:
# ports:
#   - "8001:8000"  # Backend
#   - "3001:3000"  # Frontend
```

### Issue: Worker not ingesting data

**Symptoms:**
- `/health` shows `worker_last_run` is old (>30 min)
- No new articles in database

**Diagnosis:**
```bash
docker-compose logs worker | tail -50
```

**Common causes:**

1. **Network/API errors:**
   ```
   ERROR: Failed to fetch GDELT: Connection timeout
   ```
   **Resolution:** Check internet connection, retry

2. **Rate limit exceeded:**
   ```
   ERROR: NewsAPI rate limit: 429 Too Many Requests
   ```
   **Resolution:** Wait for reset, or remove API key to skip

3. **Embedding model not downloaded:**
   ```
   ERROR: No such file or directory: 'sentence-transformers/all-MiniLM-L6-v2'
   ```
   **Resolution:** Run `make embed-cache`

4. **Database locked:**
   ```
   ERROR: database is locked
   ```
   **Resolution:** Restart services (`make down && make dev`)

### Issue: Frontend shows "Failed to fetch events"

**Symptoms:**
- UI displays error message
- Network tab shows 500 errors

**Diagnosis:**
```bash
curl http://localhost:8000/events
docker-compose logs backend | grep ERROR
```

**Common causes:**

1. **Backend not running:**
   ```bash
   docker-compose ps
   # If backend is "Exit 1", restart:
   make down && make dev
   ```

2. **Database corruption:**
   ```bash
   # Check DB integrity
   docker-compose exec backend sqlite3 /data/app.db "PRAGMA integrity_check;"
   ```
   If errors, restore from backup

3. **CORS error:**
   ```
   ERROR: CORS policy blocked
   ```
   **Resolution:** Verify `ALLOWED_ORIGINS` in `.env` includes `http://localhost:3000`

### Issue: Duplicate articles in database

**Symptoms:**
- Same URL appears multiple times
- Inflated article counts

**Diagnosis:**
```sql
SELECT url, COUNT(*) as dupes
FROM articles_raw
GROUP BY url
HAVING dupes > 1;
```

**Resolution:**
This shouldn't happen due to `UNIQUE` constraint on URL. If it does:

```sql
-- Delete duplicates, keep oldest
DELETE FROM articles_raw
WHERE id NOT IN (
  SELECT MIN(id)
  FROM articles_raw
  GROUP BY url
);
```

### Issue: Ingestion is slow (>10 min per cycle)

**Diagnosis:**
```bash
docker stats
```

**Common causes:**

1. **CPU-bound (embedding generation):**
   - Reduce batch size in `services/embed.py`
   - Skip embedding for articles older than 48h

2. **Memory pressure:**
   - Increase Docker memory limit in Docker Desktop settings
   - Restart Docker daemon

3. **Disk I/O:**
   - Move `/data` volume to SSD
   - Run `VACUUM` on database:
     ```bash
     docker-compose exec backend sqlite3 /data/app.db "VACUUM;"
     ```

### Issue: Events have unexpectedly low scores

**Diagnosis:**
```sql
SELECT id, summary, truth_score, unique_sources, evidence_flag, official_match
FROM events
WHERE truth_score < 50
ORDER BY created_at DESC
LIMIT 5;
```

**Common causes:**

1. **Low source diversity:**
   - Check if RSS feeds are being fetched
   - Verify `services/fetch/rss.py` logs

2. **No official match:**
   - Confirm NGO/Gov feeds are working:
     ```bash
     docker-compose logs worker | grep "USGS\|WHO\|NASA"
     ```

3. **Clustering too aggressive:**
   - Tune DBSCAN parameters in `services/cluster.py`:
     ```python
     eps = 0.3  # Increase to 0.4 for looser clusters
     min_samples = 3  # Decrease to 2 for smaller events
     ```

## Performance Optimization

### Speed Up Ingestion

1. **Pre-compute embeddings:**
   ```bash
   # Add this to docker-compose.yml worker command:
   command: >
     sh -c "python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer(\"sentence-transformers/all-MiniLM-L6-v2\")' &&
            python -m app.workers.scheduler"
   ```

2. **Increase batch size:**
   In `services/embed.py`:
   ```python
   embeddings = model.encode(texts, batch_size=64)  # Default: 32
   ```

3. **Reduce GDELT query window:**
   In `services/fetch/gdelt.py`:
   ```python
   window_minutes = 15  # Reduce to 10 if too much data
   ```

### Reduce Memory Usage

1. **Clear embedding cache periodically:**
   ```bash
   docker-compose exec worker rm -rf /root/.cache/torch/sentence_transformers/
   make embed-cache  # Re-download
   ```

2. **Enable database auto-vacuum:**
   ```sql
   PRAGMA auto_vacuum = FULL;
   VACUUM;
   ```

### Scale for Production

For >10k articles/day, consider:

1. **PostgreSQL instead of SQLite:**
   - Update `docker-compose.yml` to add postgres service
   - Change `DB_PATH` to connection string in `.env`

2. **Redis caching:**
   - Cache `/events` responses for 5 minutes
   - Add redis service and update backend

3. **Horizontal scaling:**
   - Run multiple worker instances with task queue (Celery)
   - Load balance backend with nginx

## Maintenance Tasks

### Daily

- Check `/health` endpoint (automated monitoring recommended)
- Review logs for errors: `docker-compose logs | grep ERROR`

### Weekly

- Backup database: `make backup` (add this to Makefile)
- Review ingestion stats in logs
- Check disk usage: `du -sh data/`

### Monthly

- Review and tune scoring thresholds based on event distribution
- Update RSS feed list (add/remove outlets)
- Check for software updates:
  ```bash
  docker-compose pull  # Update base images
  make down && make dev
  ```

### As Needed

- Rotate logs if growing too large
- Clean up old Docker images: `docker system prune -a`

## Security Hardening

For production deployment:

1. **Enable HTTPS:**
   - Add nginx reverse proxy
   - Obtain SSL cert (Let's Encrypt)

2. **Add rate limiting:**
   - Use nginx `limit_req` or FastAPI middleware

3. **Restrict CORS:**
   - Set `ALLOWED_ORIGINS` to production domain only

4. **Enable authentication:**
   - Add API key for write operations (future feature)

5. **Harden Docker:**
   - Run containers as non-root user
   - Enable Docker security scanning

## Disaster Recovery

### Scenario: Database corrupted

1. Stop all services: `make down`
2. Restore from backup: `cp backups/backup_YYYYMMDD.db data/app.db`
3. Restart: `make dev`
4. Verify health: `curl http://localhost:8000/health`

### Scenario: Server crash/reboot

1. SSH into server
2. Navigate to project: `cd /path/to/truth-layer`
3. Restart stack: `make dev`
4. Services will auto-recover from last state

### Scenario: Complete data loss

1. Rebuild from scratch: `make clean`
2. Restore database from offsite backup
3. Or re-ingest: `make dev` (worker will populate fresh data in 1-2 days)

## Support & Resources

- **Logs**: `./data/logs/` (if persistent logging enabled)
- **Database**: `./data/app.db`
- **Documentation**: `./docs/`
- **Issues**: Check GitHub Issues for known problems
- **Community**: (Add Discord/forum link if available)

## Appendix: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PATH` | Yes | `/data/app.db` | SQLite database file path |
| `NEWSAPI_KEY` | No | - | NewsAPI access key (optional) |
| `MEDIASTACK_KEY` | No | - | Mediastack access key (optional) |
| `DISCORD_WEBHOOK_URL` | No | - | Discord webhook for alerts |
| `ALLOWED_ORIGINS` | Yes | `http://localhost:3000` | CORS allowed origins |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API URL for frontend |

## Appendix: Port Mappings

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Backend | 8000 | 8000 | HTTP |
| Frontend | 3000 | 3000 | HTTP |
| Worker | N/A | N/A | N/A (background) |

## Changelog

**v1.0 (2025-10-18)**
- Initial MVP release
- 15-minute ingestion cycle
- SQLite storage
- Basic monitoring via logs
