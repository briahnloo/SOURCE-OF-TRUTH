# Truth Confidence Scoring Algorithm

## Overview

The Truth Confidence Score is a weighted metric (0-100) that quantifies the reliability of a news event based on source diversity, geographic spread, primary evidence availability, and official data matching.

**Formula:**
```
truth_score = (source_score × 0.25) +
              (geo_score × 0.40) +
              (evidence_score × 0.20) +
              (official_score × 0.15)
```

## Component Breakdown

### 1. Source Diversity Score (25%)

**Purpose**: Reward events reported by multiple independent outlets.

**Calculation:**
```python
def calculate_source_score(unique_sources: int) -> float:
    """
    Returns 0-25 points based on unique source count.
    Diminishing returns after 5 sources.
    """
    normalized = min(unique_sources / 5.0, 1.0)
    return normalized * 25
```

**Examples:**
| Unique Sources | Score | Explanation |
|----------------|-------|-------------|
| 1 | 5.0 | Single source, minimal verification |
| 3 | 15.0 | Multiple sources, moderate confidence |
| 5 | 25.0 | High diversity, maximum score |
| 10 | 25.0 | Capped at maximum (no bonus beyond 5) |

**Rationale**: Independent corroboration is the foundation of verification. Five quality sources provide sufficient coverage; additional sources add marginal value.

---

### 2. Geographic Diversity Score (40%)

**Purpose**: Prioritize events with international coverage over single-region stories.

**Calculation:**
```python
def calculate_geo_score(sources: List[str]) -> float:
    """
    Returns 0-40 points based on unique top-level domains.
    Target: 4+ unique countries for maximum score.
    """
    tlds = set()
    for source in sources:
        # Extract TLD: bbc.co.uk -> .uk, usgs.gov -> .gov
        parsed = tldextract.extract(source)
        if parsed.suffix:
            tlds.add(parsed.suffix)

    unique_countries = len(tlds)
    normalized = min(unique_countries / 4.0, 1.0)
    return normalized * 40
```

**TLD-to-Region Mapping** (simplified):
- `.gov`, `.mil` → US Government (high trust)
- `.uk`, `.co.uk` → United Kingdom
- `.fr` → France
- `.de` → Germany
- `.au` → Australia
- `.jp` → Japan
- `.org` → International (if NGO/UN)

**Examples:**
| Sources | Unique TLDs | Score | Explanation |
|---------|-------------|-------|-------------|
| `[bbc.com, cnn.com]` | 1 (.com) | 10.0 | Single region |
| `[bbc.co.uk, lemonde.fr, dw.de]` | 3 | 30.0 | Multi-country |
| `[bbc.uk, reuters.com, afp.fr, nhk.jp]` | 4+ | 40.0 | Global coverage |

**Rationale**: Events covered by outlets in multiple countries are less likely to be regional bias or propaganda. This score compensates for the omitted "independence ratio" (which required ownership data).

---

### 3. Primary Evidence Score (20%)

**Purpose**: Boost events with direct evidence from official/scientific sources.

**Calculation:**
```python
OFFICIAL_SOURCES = [
    "usgs.gov",           # Earthquakes, geology
    "who.int",            # Disease outbreaks
    "nasa.gov",           # Wildfires (FIRMS), space
    "unocha.org",         # Humanitarian crises
    "reliefweb.int"       # Disaster response
]

def calculate_evidence_score(sources: List[str]) -> float:
    """
    Returns 20 if any official source present, else 0.
    Binary flag: evidence exists or doesn't.
    """
    for source in sources:
        for official in OFFICIAL_SOURCES:
            if official in source.lower():
                return 20.0
    return 0.0
```

**Examples:**
| Scenario | Score | Explanation |
|----------|-------|-------------|
| USGS earthquake + news articles | 20.0 | Official seismic data |
| WHO outbreak alert + local press | 20.0 | Verified disease report |
| Only news articles (no official source) | 0.0 | No primary evidence |

**Rationale**: Primary evidence (government sensors, scientific instruments, official declarations) is more reliable than secondary reporting. This is a conservative binary flag—future versions could weight different evidence types.

---

### 4. Official Match Score (15%)

**Purpose**: Confirm events align temporally with official data feeds.

**Calculation:**
```python
def calculate_official_match_score(
    event_timestamp: datetime,
    official_events: List[OfficialEvent]
) -> float:
    """
    Returns 0-15 points based on temporal proximity to official event.
    Match window: ±6 hours.
    """
    for official in official_events:
        time_diff = abs((event_timestamp - official.timestamp).total_seconds())

        if time_diff <= 6 * 3600:  # 6 hours
            # Score decays with distance: perfect=15, 6h=7.5
            decay = 1 - (time_diff / (6 * 3600))
            return 15.0 * max(decay, 0.5)  # Minimum 50% if within window

    return 0.0
```

**Examples:**
| Event Type | Official Feed | Time Difference | Score | Explanation |
|------------|---------------|-----------------|-------|-------------|
| Earthquake | USGS M7.2 at 10:00 | News at 10:15 (+15 min) | 14.5 | Near-perfect match |
| Wildfire | NASA FIRMS alert 08:00 | News at 12:00 (+4h) | 10.0 | Good match |
| Outbreak | WHO bulletin 2 days ago | News today (+48h) | 0.0 | Outside 6h window |
| Political event | No official feed | N/A | 0.0 | Not applicable |

**Rationale**: Temporal alignment with official data (seismographs, satellites, health agencies) provides strong validation. Six-hour window accommodates processing/reporting delays.

---

## Confidence Tiers

Events are classified into tiers based on final truth_score:

| Tier | Score Range | Display | Criteria |
|------|-------------|---------|----------|
| **Confirmed** | 75-100 | Green badge | High source diversity + evidence or official match |
| **Developing** | 40-74 | Yellow badge | Moderate coverage, verification in progress |
| **Unverified** | 0-39 | Hidden | Single/few sources, no corroboration |

**Frontend Behavior:**
- Confirmed: Default homepage feed
- Developing: Separate tab, "Breaking" indicator
- Unverified: Not shown (prevents low-quality content)

---

## Worked Examples

### Example 1: Major Earthquake (Score: 92.5)

**Event:** Magnitude 7.2 earthquake in Pacific Ocean

**Sources:**
- usgs.gov (official)
- bbc.co.uk
- reuters.com
- afp.fr
- nhk.co.jp
- cnn.com
- aljazeera.com
- abc.net.au

**Scoring:**

1. **Source Diversity**: 8 sources
   - `min(8/5, 1.0) * 25 = 25.0`

2. **Geographic Diversity**: 6 unique TLDs (.gov, .uk, .com, .fr, .jp, .au)
   - `min(6/4, 1.0) * 40 = 40.0`

3. **Primary Evidence**: USGS present
   - `20.0`

4. **Official Match**: USGS feed timestamp within 10 minutes
   - `15.0 * 0.95 = 14.25`

**Total**: 25 + 40 + 20 + 14.25 = **92.5** (Confirmed)

---

### Example 2: Political Protest (Score: 58.0)

**Event:** Large protests in capital city

**Sources:**
- local-news.com
- twitter.com/journalist (embedded in article)
- international-outlet.com
- reddit.com/r/worldnews (discussion)

**Scoring:**

1. **Source Diversity**: 4 sources
   - `4/5 * 25 = 20.0`

2. **Geographic Diversity**: 1 TLD (.com)
   - `1/4 * 40 = 10.0`

3. **Primary Evidence**: None (no gov/NGO source)
   - `0.0`

4. **Official Match**: Not applicable
   - `0.0`

**Total**: 20 + 10 + 0 + 0 = **30.0** (Unverified → Hidden)

*Note: This event lacks corroboration and would not appear on the frontend.*

---

### Example 3: Humanitarian Crisis (Score: 68.0)

**Event:** Flooding displaces thousands in remote region

**Sources:**
- reliefweb.int (official)
- unocha.org (official)
- local-newspaper.country
- regional-tv.country

**Scoring:**

1. **Source Diversity**: 4 sources
   - `4/5 * 25 = 20.0`

2. **Geographic Diversity**: 3 TLDs (.int, .org, .country)
   - `3/4 * 40 = 30.0`

3. **Primary Evidence**: ReliefWeb + UN OCHA present
   - `20.0`

4. **Official Match**: UN OCHA situation report timestamp within 2 hours
   - `15.0 * 0.85 = 12.75`

**Total**: 20 + 30 + 20 + 12.75 = **68.0** (Developing)

*Likely flagged as "Underreported" if absent from major wires.*

---

## Calibration & Tuning

**Weights Rationale:**

| Component | Weight | Justification |
|-----------|--------|---------------|
| Source Diversity | 25% | Foundation of verification |
| Geo Diversity | 40% | Compensates for missing independence ratio, reduces regional bias |
| Primary Evidence | 20% | Direct data trumps reporting |
| Official Match | 15% | Strong validation but not always applicable |

**Threshold Tuning:**

During testing, adjust thresholds if:
- Too many "Confirmed" events (lower threshold to 80)
- Too few "Confirmed" events (lower threshold to 70)
- "Developing" tier too broad (split into two tiers: 50-74, 40-49)

**Future Enhancements:**
1. Add "Recency Bonus": Newer events get +5 points
2. "Social Verification": Count verified X/TikTok accounts as +0.5 sources
3. "Retraction Penalty": -50 points if any source issues correction
4. "Independence Map": Restore 25% weight when ownership data available

---

## API Exposure

The `/events/{id}` endpoint returns a `scoring_breakdown` object showing each component's contribution:

```json
{
  "scoring_breakdown": {
    "source_diversity": {
      "value": 25.0,
      "weight": 0.25,
      "explanation": "8 unique sources (maximum score)"
    },
    "geo_diversity": {
      "value": 40.0,
      "weight": 0.40,
      "explanation": "6 unique TLDs detected"
    },
    "primary_evidence": {
      "value": 20.0,
      "weight": 0.20,
      "explanation": "Official source present (USGS)"
    },
    "official_match": {
      "value": 14.25,
      "weight": 0.15,
      "explanation": "Matches USGS feed within 10 minutes"
    }
  },
  "truth_score": 92.5
}
```

This transparency allows users to understand **why** an event received its score.

---

## Testing

**Unit Test Coverage:**

```python
# tests/test_score.py

def test_source_diversity_capped():
    assert calculate_source_score(10) == 25.0

def test_source_diversity_fractional():
    assert calculate_source_score(3) == 15.0

def test_geo_diversity_single_country():
    sources = ["bbc.com", "cnn.com", "nytimes.com"]
    assert calculate_geo_score(sources) == 10.0

def test_evidence_flag_positive():
    sources = ["usgs.gov", "bbc.com"]
    assert calculate_evidence_score(sources) == 20.0

def test_evidence_flag_negative():
    sources = ["bbc.com", "cnn.com"]
    assert calculate_evidence_score(sources) == 0.0

def test_official_match_within_window():
    event_time = datetime(2025, 10, 18, 10, 15)
    official_time = datetime(2025, 10, 18, 10, 0)
    assert calculate_official_match_score(event_time, [Official(official_time)]) > 14.0
```

---

## Changelog

**v1.0 (MVP)**
- Initial implementation with 4-component formula
- Binary evidence flag (20 points)
- 6-hour official match window
- Skipped independence ratio (deferred to v2)

**Planned v1.1**
- Add "Social Verification" sub-score (+5% weight)
- Extend official match window to 12 hours for WHO bulletins
- Log score distributions for calibration
