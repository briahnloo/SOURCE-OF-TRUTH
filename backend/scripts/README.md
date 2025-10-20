# Backend Scripts

This directory contains database migrations and data backfill utilities.

## Migrations

Scripts for updating database schema. Run these in order when deploying new versions.

### `/migrations/migrate_add_category.py`
Adds `category` and `category_confidence` columns to the events table for event categorization.

**Usage:**
```bash
cd backend
python scripts/migrations/migrate_add_category.py
```

### `/migrations/migrate_to_postgres.py`
Migrates data from SQLite to PostgreSQL for production deployment.

**Usage:**
```bash
cd backend
python scripts/migrations/migrate_to_postgres.py
```

## Backfill Scripts

Scripts for processing existing data to add new features. These are safe to run multiple times (they skip already-processed events).

### `/backfill/backfill_categories.py`
Categorizes all events (politics, international, natural_disaster, etc.) using keyword-based classification.

**Usage:**
```bash
cd backend
python scripts/backfill/backfill_categories.py
```

### `/backfill/backfill_bias_compass.py`
Generates bias compass metrics (political/geographic/tone analysis) for events.

**Usage:**
```bash
cd backend
python scripts/backfill/backfill_bias_compass.py
```

### `/backfill/backfill_coherence.py`
Calculates narrative coherence scores and detects conflicts between sources.

**Usage:**
```bash
cd backend
python scripts/backfill/backfill_coherence.py
```

### `/backfill/backfill_perspective_excerpts.py`
Extracts representative article excerpts for each political perspective (liberal/center/conservative).

**Usage:**
```bash
cd backend
python scripts/backfill/backfill_perspective_excerpts.py
```

## Notes

- All backfill scripts check if data already exists and skip re-processing
- Run migrations before backfills
- Some scripts require API keys (set in `.env` file)
- Scripts log progress to console with emoji indicators (✅, ⚠️, ❌)

