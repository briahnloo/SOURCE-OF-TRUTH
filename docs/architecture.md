# Truth Layer Architecture

## System Overview

The Truth Layer is a three-tier application designed to aggregate, verify, and present news events with confidence scoring based on source diversity and official data matching.

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Free)                      │
├─────────────────────────────────────────────────────────────┤
│ GDELT │ RSS Feeds │ Reddit │ NewsAPI │ Mediastack │ NGO/Gov │
│       │ (20+ orgs)│  JSON  │ (opt)   │   (opt)    │ (5 orgs)│
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION WORKER                         │
│  ┌────────────┐   ┌──────────┐   ┌──────────────┐         │
│  │   Fetch    │ → │ Normalize│ → │ Deduplicate  │         │
│  │  (15 min)  │   │ Language │   │  (URL+title) │         │
│  └────────────┘   └──────────┘   └──────────────┘         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                      │
│  ┌────────────┐   ┌──────────┐   ┌──────────────┐         │
│  │   Embed    │ → │ Cluster  │ → │    Score     │         │
│  │ (Sentence- │   │ (DBSCAN) │   │ (Confidence) │         │
│  │ transformers)  │ 24h win  │   │   0-100      │         │
│  └────────────┘   └──────────┘   └──────────────┘         │
│                                           │                 │
│                                           ▼                 │
│                         ┌─────────────────────────┐         │
│                         │  Tag Underreported      │         │
│                         │  (NGO vs Major Wire)    │         │
│                         └─────────────────────────┘         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (SQLite)                         │
│  ┌────────────────┐          ┌──────────────────┐          │
│  │ articles_raw   │          │     events       │          │
│  │ (30-day TTL)   │          │  (indefinite)    │          │
│  └────────────────┘          └──────────────────┘          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                    │
│  GET /events?status=confirmed&limit=20                      │
│  GET /events/{id}                                           │
│  GET /events/underreported                                  │
│  GET /feeds/verified.xml                                    │
│  GET /health                                                │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js SSR)                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐            │
│  │ Confirmed│  │ Developing│  │ Underreported│            │
│  │  (≥75)   │  │  (40-74)  │  │   (flagged)  │            │
│  └──────────┘  └───────────┘  └──────────────┘            │
│                                                             │
│  Components: EventCard, ConfidenceMeter, EvidenceDrawer    │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Sources

**GDELT (Global Database of Events, Language, and Tone)**
- 15-minute update cycle
- Free CSV export API
- Covers global news mentions

**RSS/Atom Feeds (20+ outlets)**
- AP, Reuters, BBC, Al Jazeera, NPR, Guardian, etc.
- Parsed with feedparser
- Respects robots.txt

**Reddit JSON**
- `/r/worldnews.json`, `/r/news.json`
- No auth required for public feeds
- Rate limit: 60 req/min

**Optional APIs**
- NewsAPI (free tier: 100 req/day)
- Mediastack (free tier: 100 req/month)
- Graceful fallback if keys missing

**NGO/Government Feeds**
- ReliefWeb API (humanitarian crises)
- USGS Earthquakes (real-time seismic)
- WHO Disease Outbreak News
- NASA FIRMS (wildfire alerts)
- UN OCHA (humanitarian alerts)

### 2. Normalization Pipeline

```python
# Pseudocode
for article in raw_fetched:
    # Language detection
    if detect_language(article.text) != "en":
        continue

    # Dedupe check
    existing = db.query(Article).filter(
        (Article.url == article.url) |
        (similarity(Article.title, article.title) > 0.9)
    ).first()

    if existing:
        continue

    # Entity extraction
    doc = nlp(article.text)
    entities = [ent.text for ent in doc.ents]

    # Store
    db.add(Article(
        source=parse_domain(article.url),
        title=article.title,
        url=article.url,
        timestamp=article.published,
        entities_json=json.dumps(entities)
    ))
```

### 3. Clustering Algorithm

**Approach**: DBSCAN on sentence embeddings

```python
# Parameters
eps = 0.3              # Max cosine distance
min_samples = 3        # Min articles per cluster
window = 24 hours      # Rolling time window

# Process
articles = get_recent_articles(window)
embeddings = model.encode([a.title + " " + a.summary for a in articles])

clusters = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine').fit(embeddings)

for cluster_id in unique(clusters.labels_):
    if cluster_id == -1:  # Noise
        continue

    cluster_articles = [a for a, label in zip(articles, clusters.labels_) if label == cluster_id]
    event = create_event_summary(cluster_articles)
    db.add(event)
```

### 4. Truth Confidence Scoring

**Formula (0-100 scale)**:

```
score = (source_score * 0.25) +
        (geo_score * 0.40) +
        (evidence_score * 0.20) +
        (official_score * 0.15)
```

**Component Breakdown**:

1. **Source Diversity (25%)**:
   - Count unique domains
   - Diminishing returns: `min(sources / 5, 1.0) * 25`

2. **Geographic Diversity (40%)**:
   - Parse TLDs: .uk, .fr, .au, etc.
   - Count unique countries: `min(countries / 4, 1.0) * 40`

3. **Primary Evidence (20%)**:
   - Binary: any source in [USGS, WHO, NASA, UN, ReliefWeb]
   - Present: 20 points, Absent: 0 points

4. **Official Match (15%)**:
   - Temporal proximity to official feed event (within 6h)
   - Match: 15 points, No match: 0 points

**Confidence Tiers**:
- **Confirmed** (≥75): High source diversity + evidence
- **Developing** (40-74): Moderate coverage, no official confirmation
- **Unverified** (<40): Single source or low diversity (hidden from UI)

### 5. Underreported Detection

**Logic**:

```python
def is_underreported(event):
    # Check if present in NGO/Gov feeds
    has_ngo_source = any(
        source in ["reliefweb", "usgs", "who", "nasa", "ocha"]
        for source in event.sources
    )

    # Check if absent from major wires
    major_wires = ["ap.org", "reuters.com", "afp.com"]
    has_wire_coverage = any(
        wire in source
        for source in event.sources
        for wire in major_wires
    )

    # Flag if NGO-sourced but no wire coverage after 48h
    time_since_first = now() - event.first_seen
    return (
        has_ngo_source and
        not has_wire_coverage and
        time_since_first > timedelta(hours=48) and
        event.articles_count >= 2
    )
```

### 6. Data Retention

**Policy**:
- `articles_raw`: 30-day rolling deletion
- `events`: Kept indefinitely (aggregated metadata only)

**Implementation**:
```python
# Runs daily via APScheduler
def cleanup_old_articles():
    cutoff = datetime.now() - timedelta(days=30)
    db.query(Article).filter(Article.ingested_at < cutoff).delete()
    db.commit()
```

## Database Schema

### articles_raw
```sql
CREATE TABLE articles_raw (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,
    language TEXT,
    summary TEXT,
    text_snippet TEXT,
    entities_json TEXT,
    cluster_id INTEGER,
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cluster_id) REFERENCES events(id)
);

CREATE INDEX idx_articles_timestamp ON articles_raw(timestamp);
CREATE INDEX idx_articles_cluster ON articles_raw(cluster_id);
```

### events
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL,
    articles_count INTEGER NOT NULL,
    unique_sources INTEGER NOT NULL,
    geo_diversity REAL,
    evidence_flag BOOLEAN DEFAULT 0,
    official_match BOOLEAN DEFAULT 0,
    truth_score REAL NOT NULL,
    underreported BOOLEAN DEFAULT 0,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    languages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_score ON events(truth_score DESC);
CREATE INDEX idx_events_underreported ON events(underreported);
```

## Deployment Architecture

**Local Development** (Current):
```
docker-compose.yml
├── backend (FastAPI) → :8000
├── worker (APScheduler) → background
├── frontend (Next.js) → :3000
└── volume: ./data → /data (SQLite)
```

**Scaling Considerations** (Future):
- Replace SQLite with PostgreSQL
- Add Redis for API caching
- Separate worker pool (Celery)
- CDN for frontend static assets
- Load balancer for multiple backend instances

## Security Considerations

1. **Rate Limiting**: Per-IP throttling on API (not implemented in MVP)
2. **CORS**: Strict origin allowlist
3. **Input Validation**: Pydantic schemas for all API inputs
4. **SQL Injection**: SQLAlchemy ORM prevents raw queries
5. **XSS**: Next.js auto-escapes JSX

## Monitoring & Observability

**Logs**:
- Structured JSON logging (loguru)
- Stdout → docker-compose logs

**Health Checks**:
- `/health` endpoint returns DB status
- Frontend status pill (green/yellow/red)

**Alerting** (Optional):
- Discord webhook on worker failures
- Env-gated: only if `DISCORD_WEBHOOK_URL` set

## Performance Targets

- **Ingestion**: <5 min per 15-min cycle
- **API Latency**: <200ms p95 for /events
- **Frontend Load**: <2s first contentful paint
- **Database Size**: <500MB for 30 days of articles

## Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Backend Framework | FastAPI | Async, typed, auto-docs |
| Database | SQLite | Zero-config, sufficient for <100k articles |
| Embeddings | sentence-transformers | Local, no API costs |
| Clustering | DBSCAN | No predefined cluster count needed |
| Frontend | Next.js | SSR for SEO, React for interactivity |
| Styling | Tailwind | Rapid prototyping, small bundle |
| Orchestration | docker-compose | Simple local dev, portable |

## Known Limitations

1. **GDELT Latency**: 15-min delay typical
2. **No Real-time Updates**: Frontend requires refresh
3. **English-only**: NLP pipeline not multi-lingual
4. **No Authentication**: Public read-only API
5. **SQLite Concurrency**: Write bottleneck at scale
6. **No Image/Video Analysis**: Text-only verification
