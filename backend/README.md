# Truth Layer Backend

FastAPI-based backend service for the Truth Layer MVP.

## Features

- **Data Ingestion**: Fetches from GDELT, RSS feeds, Reddit, NGO/Gov sources
- **NLP Processing**: Entity extraction with spaCy, embeddings with sentence-transformers
- **Clustering**: DBSCAN-based event clustering
- **Truth Scoring**: Multi-factor confidence scoring (0-100)
- **Underreported Detection**: Identifies stories missing from major outlets
- **REST API**: Full-featured API with automatic OpenAPI docs
- **RSS Feed**: Generates verified events feed

## Development

### Local Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Download NLP models
python -m spacy download en_core_web_sm
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Run server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v
```

### Docker

```bash
# Build
docker build -t truth-layer-backend .

# Run
docker run -p 8000:8000 -v $(pwd)/data:/data truth-layer-backend
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py           # FastAPI app entry point
├── config.py         # Settings and configuration
├── db.py             # Database connection
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic schemas
├── routes/           # API endpoints
├── services/         # Business logic
│   ├── fetch/        # Data source fetchers
│   ├── normalize.py  # Deduplication
│   ├── embed.py      # Embeddings
│   ├── cluster.py    # Event clustering
│   ├── score.py      # Truth scoring
│   └── underreported.py
└── workers/          # Background jobs
    └── scheduler.py  # APScheduler pipeline
```

## Environment Variables

See `.env.example` in project root.

## License

MIT
