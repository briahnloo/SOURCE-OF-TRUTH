# Data Sources

This document lists all ingested data sources, their update frequencies, licenses, and implementation notes.

## News Aggregators

### GDELT (Global Database of Events, Language, and Tone)

- **URL**: https://www.gdeltproject.org/
- **Type**: Event database
- **Update Frequency**: 15 minutes
- **License**: Public domain
- **Access Method**: CSV export API
- **Coverage**: Global news mentions from 100+ countries
- **Implementation**: `services/fetch/gdelt.py`
- **Rate Limit**: None (public data)
- **Notes**: Use GDELT 2.0 Event Database, query last 15-min window

**Example Query:**
```
https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=artlist&format=json&maxrecords=250
```

## News Outlets (RSS/Atom Feeds)

### Major Wire Services

| Outlet | Feed URL | Update Freq | License |
|--------|----------|-------------|---------|
| Associated Press | `https://feeds.apnews.com/rss/` | Real-time | Fair use (headlines only) |
| Reuters | `https://www.reutersagency.com/feed/` | Real-time | Fair use (headlines only) |
| AFP (Agence France-Presse) | `https://www.afp.com/en/rss` | Real-time | Fair use (headlines only) |

### International Broadcasters

| Outlet | Feed URL | Update Freq | License |
|--------|----------|-------------|---------|
| BBC News | `http://feeds.bbci.co.uk/news/world/rss.xml` | Hourly | Fair use |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | Hourly | Fair use |
| Deutsche Welle | `https://rss.dw.com/xml/rss-en-world` | Hourly | Fair use |
| France 24 | `https://www.france24.com/en/rss` | Hourly | Fair use |
| NHK World | `https://www3.nhk.or.jp/nhkworld/en/news/rss.xml` | Hourly | Fair use |

### National Outlets

| Outlet | Feed URL | Update Freq | License |
|--------|----------|-------------|---------|
| The Guardian | `https://www.theguardian.com/world/rss` | Hourly | Fair use |
| NPR | `https://feeds.npr.org/1004/rss.xml` | Hourly | Fair use |
| CNN | `http://rss.cnn.com/rss/cnn_world.rss` | Hourly | Fair use |
| New York Times | `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` | Hourly | Fair use |
| Washington Post | `https://feeds.washingtonpost.com/rss/world` | Hourly | Fair use |

**Implementation**: `services/fetch/rss.py` using `feedparser` library

**Legal Note**: RSS feeds are designed for syndication. We store URLs and metadata only, not full article text. This constitutes fair use under copyright law.

## Social Platforms

### Reddit

- **Subreddits**: `/r/worldnews`, `/r/news`
- **Access Method**: Public JSON endpoint (no auth)
- **Update Frequency**: Every 15 minutes
- **Rate Limit**: 60 requests/minute
- **License**: User-generated content, fair use for aggregation
- **Implementation**: `services/fetch/reddit.py`

**Example URLs:**
```
https://www.reddit.com/r/worldnews.json?limit=25
https://www.reddit.com/r/news.json?limit=25
```

**Notes**:
- Only extract post titles and URLs
- Filter for posts with external links
- Ignore self-posts and comments

## Optional Commercial APIs

### NewsAPI

- **URL**: https://newsapi.org/
- **Type**: News aggregator API
- **Free Tier**: 100 requests/day
- **License**: Attribution required
- **Access Method**: REST API with key
- **Implementation**: `services/fetch/newsapi.py`
- **Graceful Degradation**: Skip if `NEWSAPI_KEY` not set

**Rate Limit**: 100 req/day (free), 1 req/sec

**Example:**
```bash
curl "https://newsapi.org/v2/top-headlines?category=general&apiKey=YOUR_KEY"
```

### Mediastack

- **URL**: https://mediastack.com/
- **Type**: News API
- **Free Tier**: 100 requests/month
- **License**: Attribution required
- **Access Method**: REST API with key
- **Implementation**: `services/fetch/mediastack.py`
- **Graceful Degradation**: Skip if `MEDIASTACK_KEY` not set

**Rate Limit**: 100 req/month (free)

**Example:**
```bash
curl "http://api.mediastack.com/v1/news?access_key=YOUR_KEY&languages=en"
```

## NGO & Government Feeds

### ReliefWeb (UN OCHA)

- **URL**: https://reliefweb.int/
- **Type**: Humanitarian news and reports
- **Access Method**: Public API (no key required)
- **Update Frequency**: Hourly
- **License**: Creative Commons (varies by report)
- **Coverage**: Disasters, conflicts, humanitarian crises
- **Implementation**: `services/fetch/ngos_usgs_who_nasa_ocha.py`

**API Endpoint:**
```
https://api.reliefweb.int/v1/reports?appname=truthlayer&limit=50
```

**Fields**: title, date, country, disaster_type, source

### USGS Earthquake Hazards Program

- **URL**: https://earthquake.usgs.gov/
- **Type**: Real-time earthquake data
- **Access Method**: GeoJSON feed (public)
- **Update Frequency**: Real-time (1-5 min delay)
- **License**: Public domain (US Government)
- **Coverage**: Global seismic events
- **Implementation**: `services/fetch/ngos_usgs_who_nasa_ocha.py`

**Feed URL:**
```
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
```

**Fields**: magnitude, location, time, depth, tsunami_flag

### WHO Disease Outbreak News (DON)

- **URL**: https://www.who.int/emergencies/disease-outbreak-news
- **Type**: Official disease outbreak alerts
- **Access Method**: RSS feed
- **Update Frequency**: As outbreaks occur (irregular)
- **License**: WHO terms of use (attribution, non-commercial)
- **Coverage**: Global public health emergencies
- **Implementation**: `services/fetch/ngos_usgs_who_nasa_ocha.py`

**Feed URL:**
```
https://www.who.int/feeds/entity/csr/don/en/rss.xml
```

**Fields**: title, date, country, disease, description

### NASA FIRMS (Fire Information for Resource Management System)

- **URL**: https://firms.modaps.eosdis.nasa.gov/
- **Type**: Active wildfire alerts
- **Access Method**: Public API (MAP_KEY required, free)
- **Update Frequency**: 3 hours (satellite revisit time)
- **License**: Public domain (NASA)
- **Coverage**: Global wildfire detections
- **Implementation**: `services/fetch/ngos_usgs_who_nasa_ocha.py`

**API Endpoint:**
```
https://firms.modaps.eosdis.nasa.gov/api/area/csv/MAP_KEY/VIIRS_SNPP_NRT/world/1
```

**Fields**: latitude, longitude, brightness, confidence, acq_date

**Note**: Request free MAP_KEY at https://firms.modaps.eosdis.nasa.gov/api/

### UN OCHA Humanitarian Data Exchange (HDX)

- **URL**: https://data.humdata.org/
- **Type**: Humanitarian datasets and alerts
- **Access Method**: CKAN API (no key required)
- **Update Frequency**: Varies by dataset
- **License**: Varies (mostly CC-BY)
- **Coverage**: Conflicts, disasters, population data
- **Implementation**: `services/fetch/ngos_usgs_who_nasa_ocha.py`

**API Endpoint:**
```
https://data.humdata.org/api/3/action/package_search?q=crisis
```

**Fields**: title, organization, updated_date, location

## Data Retention & Compliance

### Storage Policy

- **Raw Articles**: 30 days (then auto-deleted)
- **Events**: Indefinite (aggregated metadata only)
- **URLs**: Stored permanently (for source attribution)
- **Article Text**: Only snippets (100-200 chars), not full content

### Legal Compliance

1. **Fair Use**: We aggregate headlines and metadata for news verification, a transformative non-commercial purpose.
2. **Attribution**: All sources credited with domain name and direct link.
3. **robots.txt**: Respect crawl directives (use RSS feeds, not scraping).
4. **Copyright**: No full-text storage; links back to original publishers.
5. **Privacy**: No personal data collected; all sources are public.

### GDPR & Privacy

- No user accounts or personal data in MVP
- No cookies except essential session management
- No third-party tracking scripts
- IP addresses not logged or stored

## Source Quality Tiers

For scoring purposes, sources are grouped into trust tiers:

### Tier 1: Official/Scientific (20% score boost)
- USGS, WHO, NASA, UN OCHA, ReliefWeb
- Government agencies (.gov, .mil)

### Tier 2: Major Wire Services
- AP, Reuters, AFP
- Used for "underreported" baseline comparison

### Tier 3: Established Outlets
- BBC, Guardian, NPR, Al Jazeera, etc.
- Counted equally in source diversity

### Tier 4: Social/Aggregators
- Reddit, GDELT mentions
- Lower weight (0.5× in source count)

## Adding New Sources

To add a new RSS feed:

1. Verify license allows aggregation
2. Add URL to `RSS_FEEDS` list in `services/fetch/rss.py`
3. Test with `make ingest-once`
4. Update this document

To add a new API source:

1. Check rate limits and free tier availability
2. Create fetcher module in `services/fetch/`
3. Add env var to `.env.example` if key required
4. Implement graceful fallback if key missing
5. Add unit tests in `tests/test_fetch.py`
6. Update this document

## Monitoring Source Health

The worker logs ingestion stats per source:

```
[2025-10-18 14:30:00] INFO: Ingestion complete
  - GDELT: 234 articles
  - RSS feeds: 156 articles
  - Reddit: 23 articles
  - USGS: 3 events
  - WHO: 0 events
  - NASA FIRMS: 12 events
  - ReliefWeb: 8 reports
  - Total: 436 new articles
```

If a source consistently returns 0 results:
- Check API endpoint status
- Verify rate limits not exceeded
- Review logs for errors
- Temporarily disable in code if broken

## License Summary

| Source Type | License | Commercial Use | Attribution Required |
|-------------|---------|----------------|----------------------|
| GDELT | Public Domain | Yes | No |
| RSS Feeds | Fair Use | No (non-commercial) | Yes |
| Reddit | Fair Use | No (non-commercial) | Yes |
| NewsAPI | Proprietary | No (free tier) | Yes |
| Mediastack | Proprietary | No (free tier) | Yes |
| USGS | Public Domain | Yes | No |
| WHO | CC-BY-NC-SA | No | Yes |
| NASA | Public Domain | Yes | No |
| UN OCHA | CC-BY | Yes | Yes |
| ReliefWeb | Varies | Varies | Yes |

**Recommendation**: This MVP is strictly non-commercial. For commercial deployment, review each source's ToS and obtain necessary licenses.
