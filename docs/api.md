# API Reference

Base URL: `http://localhost:8000`

## Health Check

### GET /health

Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "worker_last_run": "2025-10-18T14:30:00Z",
  "total_events": 1234,
  "total_articles": 5678
}
```

## Events

### GET /events

Retrieve paginated list of events.

**Query Parameters:**
- `status` (optional): Filter by confidence tier
  - Values: `confirmed`, `developing`, `all`
  - Default: `all`
- `limit` (optional): Results per page (1-100)
  - Default: `20`
- `offset` (optional): Pagination offset
  - Default: `0`
- `underreported` (optional): Filter underreported events
  - Values: `true`, `false`
  - Default: `false`

**Example Request:**
```bash
curl "http://localhost:8000/events?status=confirmed&limit=10&offset=0"
```

**Response:**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "id": 123,
      "summary": "Major earthquake strikes Pacific region, magnitude 7.2",
      "articles_count": 15,
      "unique_sources": 8,
      "truth_score": 92.5,
      "confidence_tier": "confirmed",
      "underreported": false,
      "first_seen": "2025-10-18T10:00:00Z",
      "last_seen": "2025-10-18T14:00:00Z",
      "evidence": {
        "source_diversity": 25,
        "geo_diversity": 40,
        "primary_evidence": 20,
        "official_match": 7.5
      },
      "sources": [
        {"domain": "usgs.gov", "title": "M7.2 - Pacific Ocean"},
        {"domain": "bbc.com", "title": "Earthquake triggers tsunami warning"},
        {"domain": "reuters.com", "title": "Pacific nations on alert after quake"}
      ]
    }
  ]
}
```

### GET /events/{id}

Retrieve detailed information for a specific event.

**Path Parameters:**
- `id` (required): Event ID

**Example Request:**
```bash
curl "http://localhost:8000/events/123"
```

**Response:**
```json
{
  "id": 123,
  "summary": "Major earthquake strikes Pacific region, magnitude 7.2",
  "articles_count": 15,
  "unique_sources": 8,
  "geo_diversity": 0.85,
  "evidence_flag": true,
  "official_match": true,
  "truth_score": 92.5,
  "confidence_tier": "confirmed",
  "underreported": false,
  "first_seen": "2025-10-18T10:00:00Z",
  "last_seen": "2025-10-18T14:00:00Z",
  "languages": ["en"],
  "created_at": "2025-10-18T10:15:00Z",
  "articles": [
    {
      "id": 456,
      "source": "usgs.gov",
      "title": "M7.2 - Pacific Ocean",
      "url": "https://earthquake.usgs.gov/earthquakes/eventpage/...",
      "timestamp": "2025-10-18T10:00:00Z",
      "summary": "A magnitude 7.2 earthquake occurred...",
      "entities": ["Pacific Ocean", "tsunami", "magnitude 7.2"]
    },
    {
      "id": 457,
      "source": "bbc.com",
      "title": "Earthquake triggers tsunami warning",
      "url": "https://bbc.com/news/world-...",
      "timestamp": "2025-10-18T10:30:00Z",
      "summary": "Authorities issued tsunami warnings...",
      "entities": ["earthquake", "tsunami", "Pacific"]
    }
  ],
  "scoring_breakdown": {
    "source_diversity": {
      "value": 25,
      "weight": 0.25,
      "explanation": "8 unique sources (maximum score)"
    },
    "geo_diversity": {
      "value": 34,
      "weight": 0.40,
      "explanation": "5 unique TLDs (.gov, .com, .uk, .au, .jp)"
    },
    "primary_evidence": {
      "value": 20,
      "weight": 0.20,
      "explanation": "Official source present (USGS)"
    },
    "official_match": {
      "value": 13.5,
      "weight": 0.15,
      "explanation": "Matches USGS earthquake feed (90% confidence)"
    }
  }
}
```

### GET /events/underreported

Retrieve events flagged as underreported.

**Query Parameters:**
- `limit` (optional): Results per page (1-100)
  - Default: `20`
- `offset` (optional): Pagination offset
  - Default: `0`

**Example Request:**
```bash
curl "http://localhost:8000/events/underreported?limit=5"
```

**Response:**
```json
{
  "total": 12,
  "limit": 5,
  "offset": 0,
  "results": [
    {
      "id": 789,
      "summary": "Humanitarian crisis in remote region, aid agencies respond",
      "articles_count": 4,
      "unique_sources": 3,
      "truth_score": 68.0,
      "confidence_tier": "developing",
      "underreported": true,
      "first_seen": "2025-10-16T08:00:00Z",
      "last_seen": "2025-10-17T12:00:00Z",
      "reason": "Present in ReliefWeb and UN OCHA, absent from major wire services for 48+ hours",
      "sources": [
        {"domain": "reliefweb.int", "title": "Emergency response activated"},
        {"domain": "unocha.org", "title": "Humanitarian needs assessment"},
        {"domain": "local-news-outlet.com", "title": "Aid arrives in affected area"}
      ]
    }
  ]
}
```

## Statistics

### GET /stats/summary

Retrieve aggregate statistics.

**Response:**
```json
{
  "total_events": 1234,
  "total_articles": 5678,
  "confirmed_events": 345,
  "developing_events": 678,
  "underreported_events": 23,
  "avg_confidence_score": 62.4,
  "last_ingestion": "2025-10-18T14:30:00Z",
  "sources_count": 42,
  "coverage_by_tier": {
    "confirmed": 345,
    "developing": 678,
    "unverified": 211
  },
  "top_sources": [
    {"domain": "reuters.com", "article_count": 234},
    {"domain": "bbc.com", "article_count": 198},
    {"domain": "ap.org", "article_count": 176}
  ]
}
```

## RSS Feed

### GET /feeds/verified.xml

Returns RSS 2.0 feed of confirmed and developing events from the last 48 hours.

**Example Request:**
```bash
curl "http://localhost:8000/feeds/verified.xml"
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Truthboard - Verified Events</title>
    <link>http://localhost:3000</link>
    <description>Truth-scored news events verified via open data sources</description>
    <language>en</language>
    <lastBuildDate>Sat, 18 Oct 2025 14:30:00 +0000</lastBuildDate>
    <atom:link href="http://localhost:8000/feeds/verified.xml" rel="self" type="application/rss+xml"/>

    <item>
      <title>Major earthquake strikes Pacific region, magnitude 7.2</title>
      <link>http://localhost:3000/events/123</link>
      <description>Event verified with confidence score 92.5 from 8 sources including USGS</description>
      <pubDate>Sat, 18 Oct 2025 10:00:00 +0000</pubDate>
      <guid isPermaLink="true">http://localhost:3000/events/123</guid>
      <category>Confirmed</category>
    </item>
  </channel>
</rss>
```

## Error Responses

All endpoints return standard HTTP status codes:

**400 Bad Request:**
```json
{
  "detail": "Invalid status parameter. Must be 'confirmed', 'developing', or 'all'."
}
```

**404 Not Found:**
```json
{
  "detail": "Event with id 999 not found."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Database connection error. Please try again later."
}
```

## Rate Limiting

Currently no rate limiting enforced in MVP. Future implementation will use:
- 100 requests per minute per IP
- 429 status code when exceeded

## CORS Policy

Allowed origins configured via `ALLOWED_ORIGINS` environment variable.

Default: `http://localhost:3000`

## Versioning

API version: `v1` (implicit, no prefix required for MVP)

Future versions will use path prefix: `/api/v2/events`
