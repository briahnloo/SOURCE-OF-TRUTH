# Article Ranking Logic Analysis & Optimization Report

**Analysis Date:** 2024-11-20
**Files Analyzed:** `ranking.py`, `events.py`, `conflict_priority.py`
**Status:** Comprehensive review completed

---

## Executive Summary

Your ranking system is **well-designed with sophisticated three-phase logic**, but there are **key issues with optimality** and **inconsistencies across sections** that should be addressed:

### Critical Issues Found:
1. **Conflicts section uses completely different ranking** (conflict_priority.py) - NOT using main ranking system
2. **Recency weights are TOO HIGH** in some sections (70% for developing stories)
3. **Importance decay is EXPONENTIAL but aggressive** - may be too steep
4. **Story momentum penalties are too harsh** (-15% for stale stories)
5. **Diversity bonus applied AFTER sorting** - reduces its effectiveness
6. **Two-pass ranking is inefficient** - recalculates scores unnecessarily

### Overall Assessment:
- ✅ **Strengths:** Multi-phase approach, exponential decay, category diversity, tier-specific weights
- ❌ **Weaknesses:** Inconsistent across sections, overly aggressive on recency, conflicts uses different logic
- ⚠️ **Risks:** Fresh but unimportant articles dominate, old important stories disappear too quickly

---

## Current Ranking System Architecture

### System Overview
```
Frontend Requests
       ↓
┌──────────────────────────────────────────────────┐
│        API Endpoints (events.py)                 │
├──────────────────────────────────────────────────┤
│ GET /events          → rank_events()             │
│ GET /events/search   → rank_events()             │
│ GET /events/conflicts → calculate_conflict_priority() ⚠️ DIFFERENT
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│  Ranking Modules                                 │
├──────────────────────────────────────────────────┤
│ ranking.py:           3-phase ranking system     │
│ conflict_priority.py: Separate conflict logic    │
└──────────────────────────────────────────────────┘
       ↓
Database Results
```

---

## Detailed Component Analysis

### 1. RANKING.PY - Main Ranking System

#### A. Phase 1: Reweighting & Decay Curves

**Current Weight Distribution (by tier):**
| Tier | Recency | Importance | Quality |
|------|---------|-----------|---------|
| Confirmed | 60% | 20% | 20% |
| Developing | 70% | 15% | 15% |
| Conflicts | 55% | 25% | 20% |
| All/Search | 65% | 15% | 20% |

**Analysis:**
- ✅ **Positive:** Different weights for different contexts (section-aware)
- ❌ **Issue #1:** 70% recency for "developing" is TOO HIGH
  - This makes developing stories PURELY recency-driven
  - Means a trivial breaking news beats established developing story
  - Importance/quality nearly irrelevant (30% combined)

- ⚠️ **Issue #2:** 65% recency for "all" might still be high
  - Means old but highly important events fade quickly
  - Example: Major political scandal from 2 weeks ago gets buried below today's minor news

**Exponential Importance Decay:**
```
Formula: importance × e^(-hours_old/120)

Timeline:
- 0h:   100%  (baseline)
- 24h:  82%   (1 day old)
- 72h:  53%   (3 days old)
- 120h: 37%   (5 days old) ← Half-life
- 168h: 25%   (7 days old)
- 240h: 8%    (10 days old)
```

**Analysis:**
- ✅ **Positive:** Exponential is better than linear (steeper decay)
- ❌ **Issue #3:** Half-life of 120 hours (5 days) is AGGRESSIVE
  - Old but crucial stories lose 63% importance in 5 days
  - Combined with 55-70% recency weight, old important news becomes invisible
  - Compare: Newspaper archives keep important stories available indefinitely

**Recency Score Brackets:**
```
0-4h:   1.0    (breaking news)
4-12h:  0.90   (fresh)
12-24h: 0.70   (same day)
24-48h: 0.45   (two days)
48-72h: 0.20   (stale)
72h+:   0.05 × e^(-hours/180)  (severe decay)
```

**Analysis:**
- ✅ **Positive:** Steep drops enforce freshness (prevents stale news dominating)
- ❌ **Issue #4:** Drop from 0.70 → 0.45 between 12-48h is TOO SHARP
  - Article from 25 hours ago loses 36% of recency score
  - Creates artificial cliff where "same day" news dramatically outweighs "2-day-old" news

- ❌ **Issue #5:** After 72h, exponential decay is VERY STEEP (half-life 180h)
  - 7-day-old story has recency score of ~0.005
  - At 15 days old: essentially invisible (~0.00001)
  - Makes covering ongoing stories impossible

---

#### B. Phase 2: Story Momentum & Diversity Bonus

**Story Momentum (lines 145-173):**
```python
if hours_old <= 24 and articles >= 5:
    boost = 1.08  # +8% for actively developing

if hours_old > 72 and articles <= 2:
    penalty = 0.85  # -15% for stale/dead stories
```

**Analysis:**
- ✅ **Positive:** Promotes actively developing stories
- ❌ **Issue #6:** -15% penalty for old stories with few articles is HARSH
  - Applies to ALL events > 72h with ≤2 articles
  - Example: Important ongoing investigation with new article every 2-3 days gets penalized
  - The story might still be important but slow-moving

- ❌ **Issue #7:** Bonus/penalty is MULTIPLIED (affects final score)
  - Not additive, so it compounds with other factors
  - A fresh unimportant story: 1.08× multiplier on low score might still rank high
  - An old important story: 0.85× multiplier makes it essentially disappear

**Diversity Bonus (lines 176-225):**
```python
Position 1-3:    +3% if different category
Position 4-20:   +10-15% if category absent/underrepresented
Position 20+:    +15% if category absent
```

**Analysis:**
- ✅ **Positive:** Prevents category monopolies (e.g., all politics)
- ❌ **Issue #8:** Diversity bonus applied AFTER sorting
  - First pass sorts events without category info
  - Second pass recalculates with diversity
  - Creates instability and inefficiency
  - Bonus can dramatically shift positions (10-15% is large)

- ⚠️ **Issue #9:** Only looks at top 10 for diversity distribution
  - What if there are 5 categories in top 10?
  - A 6th category at position 15 can boost dramatically
  - Creates unpredictable jumps in ranking

---

#### C. Phase 3: Section-Specific Weights

Currently implemented as:
```python
tier_weights = {
    'confirmed': {importance: 0.20, quality: 0.20, recency: 0.60},
    'developing': {importance: 0.15, quality: 0.15, recency: 0.70},
    'conflicts': {importance: 0.25, quality: 0.20, recency: 0.55},
    'all': {importance: 0.15, quality: 0.20, recency: 0.65},
}
```

**Analysis:**
- ✅ **Positive:** Different sections get context-appropriate weights
- ⚠️ **Issue #10:** "Conflicts" tier weights NOT actually used
  - `get_conflict_events()` in events.py uses `calculate_conflict_priority()` instead
  - Phase 3 conflicts weights are dead code
  - Creates inconsistency: different ranking logic for conflicts

---

### 2. CONFLICT_PRIORITY.PY - Separate Ranking System

**Weight Distribution:**
```
40% - Conflict Severity (from coherence score)
35% - Issue Importance (category + coverage)
25% - Recency (time decay)
Total: 100%
```

**Analysis:**
- ✅ **Positive:** Specifically designed for conflicts (severity matters most)
- ❌ **Issue #10 (Part 2):** INCONSISTENT with main ranking system
  - Main system: 65% recency (for "all" tier)
  - Conflicts: 25% recency
  - Same event might rank differently in /events/all vs /events/conflicts

- ⚠️ **Issue #11:** Recency decay is SLOWER but less sophisticated
  - Uses hardcoded brackets (4h, 8h, 12h, 24h, 48h, 72h+)
  - After 72h: linear decay (0.2 per day lost)
  - No exponential decay like main system

- ⚠️ **Issue #12:** Severity calculation is indirect
  - Uses coherence score (0-100, inverted)
  - But coherence < 30 already gets 30-40 points
  - Coherence 50-70 gets 10-20 points
  - Non-linear scoring makes small differences in coherence create big score gaps

---

### 3. EVENTS.PY API Endpoints

**Endpoint Analysis:**

| Endpoint | Tier Used | Ranking Function | Issues |
|----------|-----------|------------------|--------|
| GET /events | status parameter | rank_events() | Works correctly |
| GET /events/search | 'all' tier | rank_events() | Works correctly |
| GET /events/conflicts | N/A | calculate_conflict_priority() | ❌ Different system |

**Specific Issues in /events/conflicts:**

1. **Line 492-498:** Fetches 4x results then filters
   ```python
   events = query.limit(limit * 4).offset(offset).all()
   ```
   - Problem: Offset applied to oversized result set
   - User requests offset=0, limit=20 but system fetches first 80, then applies filters
   - This breaks pagination logic

2. **Line 501-605:** Complex multi-step filtering
   - Manually filters foreign elections, non-political topics
   - Additional political diversity checks
   - Creates unpredictable exclusions

3. **Line 643-649:** Priority calculation done on filtered results
   - Conflicts found AFTER pagination
   - Means ranking within each page, not across all conflicts

---

## Issues Summary & Impact Analysis

### Critical Issues (🔴 High Priority)

| # | Issue | Impact | Location |
|---|-------|--------|----------|
| 1 | Conflicts uses different ranking system | Inconsistent ranking across sections | conflict_priority.py vs ranking.py |
| 2 | 70% recency for developing is TOO HIGH | Trivial fresh news beats important stories | ranking.py:281 |
| 3 | Importance half-life is 5 days | Old important stories fade too quickly | ranking.py:48 |
| 4 | Recency brackets have sharp drops | Creates artificial cliffs (0.70→0.45) | ranking.py:84-98 |
| 5 | Story momentum penalty is -15% | Harsh on slow-moving important stories | ranking.py:171 |

### Medium Issues (🟡 Medium Priority)

| # | Issue | Impact | Location |
|---|-------|--------|----------|
| 6 | Momentum is multiplicative | Compounds with other factors | ranking.py:307 |
| 7 | Diversity bonus applied after sorting | Creates instability, inefficiency | ranking.py:336-368 |
| 8 | Only looks at top 10 for diversity | Unpredictable boost patterns | ranking.py:139 |
| 9 | Conflicts pagination broken | User sees wrong results at different pages | events.py:492-498 |
| 10 | Conflicts recency decay is simpler | Less sophisticated than main system | conflict_priority.py:137-155 |

### Low Issues (🟢 Low Priority)

| # | Issue | Impact | Location |
|---|-------|--------|----------|
| 11 | Two-pass ranking is inefficient | Recalculates scores unnecessarily | ranking.py:336-368 |
| 12 | Dead code for conflicts weights | Confusing, suggests incomplete refactor | ranking.py:278-282 |

---

## Comparative Analysis: News Rankings vs Your System

### How Traditional News Sites Balance Freshness & Importance

**NY Times / CNN Approach:**
- **Homepage:** 70% recency, 30% importance (latest news first, but quality matters)
- **Section Pages:** 60% recency, 40% importance (balanced)
- **Archives:** 20% recency, 80% importance (old major stories stay prominent)

**Your System:**
- **Developing:** 70% recency, 30% importance ✓ Similar to homepage
- **Confirmed:** 60% recency, 40% importance ✓ Similar to section pages
- **Search:** 65% recency, 35% importance ✓ Reasonable
- **All:** 65% recency, 35% importance ✓ Reasonable
- **Conflicts:** 25% recency, 75% importance ✓ Good for ongoing conflicts

**Verdict:** Weight distribution is actually REASONABLE. The problem is:
- **Exponential decay on importance** (aggressive half-life of 5 days)
- **Sharp recency brackets** (huge drops between time brackets)
- **These two combined** = old important stories disappear too quickly

---

## What Works Well ✅

1. **Tier-aware weights** - Different sections get appropriate weights
2. **Exponential decay** - Better than linear for both importance and recency
3. **Category diversity** - Prevents news monopoly by one topic
4. **Story momentum** - Promotes actively developing stories
5. **Multi-phase approach** - Sophisticated, covers multiple factors
6. **Quality scoring** - Balances truth score + source diversity
7. **Coherence-based conflict severity** - Good for conflicts section

---

## What Needs Improvement ❌

### High-Impact Issues

**1. Recency Weight Too Aggressive for Developing**
- **Problem:** 70% recency means importance/quality nearly irrelevant
- **Effect:** Trivial breaking news (e.g., "Mayor announces new park") beats genuine developing story
- **Solution:** Reduce to 55-60% recency for developing

**2. Importance Decay Too Steep**
- **Problem:** Half-life of 5 days means old stories disappear
- **Effect:** Major investigation that's 2 weeks old becomes invisible
- **Example:** Story from 10 days ago has only 8% importance weight
- **Solution:** Increase half-life to 7-10 days (stretch over 2-3 weeks instead of 5 days)

**3. Recency Brackets Have Sharp Cliffs**
- **Problem:** 0.70 → 0.45 between 12-48h is too steep
- **Effect:** Article from 25 hours ago loses 36% of recency score
- **Solution:** Use smoother curve (logarithmic) or smaller increments

**4. Story Momentum Penalty Too Harsh**
- **Problem:** -15% penalty for old stories with few articles
- **Effect:** Penalizes slow-moving but important stories (investigations, ongoing events)
- **Solution:** Reduce to -5% and only apply if article count is 0-1 (truly stale)

**5. Conflicts Uses Completely Different System**
- **Problem:** Not using main rank_events() function
- **Effect:** Inconsistent behavior, conflicts page ranks differently than search
- **Solution:** Integrate conflicts into main ranking system OR add 'conflicts' tier to rank_events()

---

## Recommended Improvements

### Quick Wins (Low Risk, High Impact)

#### 1. Reduce Recency Weight for Developing Stories
**File:** `ranking.py:281`
```python
# CHANGE FROM:
'developing': {'importance': 0.15, 'quality': 0.15, 'recency': 0.70},

# CHANGE TO:
'developing': {'importance': 0.20, 'quality': 0.15, 'recency': 0.65},
```
**Why:** Still prioritizes freshness but allows importance to matter
**Impact:** Important developing stories won't disappear, but fresh news still leads
**Risk:** Low - still emphasizes recency

---

#### 2. Lengthen Importance Decay Half-Life
**File:** `ranking.py:48`
```python
# CHANGE FROM:
decay_factor = math.exp(-hours_old / 120)  # 5-day half-life

# CHANGE TO:
decay_factor = math.exp(-hours_old / 168)  # 7-day half-life (168 hours)
```
**Why:** Important stories should stay relevant longer
**Impact:** Major stories (investigations, ongoing events) stay visible 2-3 weeks
**Effect on Timeline:**
- 72 hours (3 days): 63% → 71% (10% more importance retained)
- 168 hours (7 days): 25% → 50% (2x more importance after 1 week)
- 240 hours (10 days): 8% → 20% (2.5x more importance after 10 days)
**Risk:** Low - importance still decays, just more gradually

---

#### 3. Smooth Recency Brackets with Logarithmic Decay
**File:** `ranking.py:54-98`
```python
# CHANGE FROM harsh brackets to smooth curve:
def calculate_recency_score(event: Event) -> float:
    now = datetime.utcnow()
    hours_old = (now - event.last_seen).total_seconds() / 3600

    # Smooth logarithmic decay instead of harsh brackets
    # Peak at 0-4 hours, then smooth decline
    if hours_old <= 4:
        return 1.0  # Breaking news
    else:
        # Smooth decay after 4 hours
        # At 24h: 0.60 (instead of 0.70)
        # At 72h: 0.15 (instead of 0.20)
        # At 168h: 0.03 (instead of 0.005)
        return 0.8 * math.exp(-(hours_old - 4) / 48)
```
**Why:** Prevents sharp drops that create artificial cliffs
**Impact:** Smoother ranking transitions, older stories don't suddenly drop
**Risk:** Low-Medium - changes decay curve but maintains freshness priority

---

#### 4. Reduce Story Momentum Penalty
**File:** `ranking.py:170-171`
```python
# CHANGE FROM:
if hours_old > 72 and articles <= 2:
    return 0.85  # 15% penalty

# CHANGE TO:
if hours_old > 72 and articles == 0:  # Only if truly no new articles
    return 0.90  # 10% penalty (less harsh)
```
**Why:** Penalize truly stale (no articles), not just slow-moving (1-2 articles)
**Impact:** Investigations and slow stories get fair ranking
**Risk:** Low - only affects truly stale stories

---

### Medium Priority Improvements

#### 5. Fix Conflicts Ranking Inconsistency
**Problem:** /events/conflicts uses different system than /events/all

**Option A: Integrate into Main System (Recommended)**
```python
# In ranking.py, add conflicts tier:
tier_weights = {
    'confirmed': {'importance': 0.20, 'quality': 0.20, 'recency': 0.60},
    'developing': {'importance': 0.20, 'quality': 0.15, 'recency': 0.65},  # Fixed
    'conflicts': {'importance': 0.40, 'quality': 0.15, 'recency': 0.45},  # New tier
    'all': {'importance': 0.15, 'quality': 0.20, 'recency': 0.65},
}
```

Then in `events.py`, change conflicts endpoint:
```python
# Instead of: calculate_conflict_priority(event)
# Use: rank_events(all_events, confidence_tier='conflicts')
```

**Why:** Unified ranking logic, consistent behavior
**Risk:** Medium - need to test that conflicts rank appropriately

---

#### 6. Fix Conflicts Pagination
**File:** `events.py:492-498`
```python
# CHANGE FROM:
events = (
    query.order_by(Event.last_seen.desc())
    .limit(limit * 4)  # Problem: applies offset to oversized set
    .offset(offset)
    .all()
)

# CHANGE TO:
# Don't oversample - apply filters BEFORE pagination
# Filter during query, not after:
events = query.all()  # Get all candidates
events = filter_political_events(events)  # Filter
events_sorted = rank_events(events, confidence_tier='conflicts')
events = events_sorted[offset:offset + limit]  # Paginate
```

**Why:** Correct pagination semantics
**Risk:** Medium - need to verify all conflicts are properly filtered

---

### Advanced Improvements (Lower Priority)

#### 7. Optimize Two-Pass Ranking
**Current approach:**
1. First pass: Score without diversity info
2. Sort
3. Calculate diversity distribution
4. Second pass: Recalculate with diversity
5. Re-sort

**Optimized approach:**
1. Single pass: Calculate all scores with estimated diversity
2. Sort once
3. Post-processing: Small adjustments only if needed

**Impact:** Slightly faster, less confusing
**Risk:** Low-Medium - refactoring complexity

---

#### 8. Make Diversity Bonus Additive Instead of Multiplicative
**Current:**
```python
final_score = balanced_score * diversity_bonus  # Multiplicative
```

**Better:**
```python
# Additive bonus (max 0.05 or 5 points added)
final_score = balanced_score + (diversity_bonus - 1.0) * balanced_score * 0.5
```

**Why:** Prevents compounding effects, more predictable
**Risk:** Medium - changes score distribution

---

## Testing Recommendations

Before implementing changes, test these scenarios:

### Test Case 1: Fresh Minor vs Old Major Story
```
Article A: "New coffee shop opens downtown"
- Age: 2 hours old
- Importance: 10
- Sources: 2
- Category: other

Article B: "Major corruption scandal in city council"
- Age: 8 days old
- Importance: 80
- Sources: 8
- Category: politics
```

**Current System:**
- A likely ranks higher (breaking news, 2h old)

**Desired:**
- B should rank higher (major importance outweighs age)

**Test Implementation:**
```python
# Add to test suite
def test_old_major_beats_fresh_minor():
    article_a = create_test_event(age_hours=2, importance=10, sources=2)
    article_b = create_test_event(age_hours=192, importance=80, sources=8)

    ranked = rank_events([article_a, article_b], confidence_tier='confirmed')
    assert ranked[0].importance_score == 80, "Old major should rank first"
```

### Test Case 2: Ongoing Investigation (Slow Moving)
```
Investigation Event:
- Age: 15 days old
- Articles: 1 new article today, then 1 every 3 days
- Importance: 75
- Category: crime
```

**Current System:**
- Gets -15% momentum penalty (15 days old, ≤2 articles)
- Gets very low importance (8% at 10 days)

**Desired:**
- Should still be visible (important ongoing story)

**Test Implementation:**
```python
def test_slow_moving_investigation():
    investigation = create_test_event(
        age_hours=360,  # 15 days
        articles=20,    # Many articles total, but added slowly
        importance=75,
        category='crime'
    )

    ranked = rank_events([investigation, ...other_events...], tier='all')
    # Should be in top 30, not buried below
    assert ranked.index(investigation) < 30
```

### Test Case 3: Developing vs Confirmed Tier Difference
```
Same event, ranked in both tiers
```

**Expected:**
- Developing: Higher recency priority (freshness of break is key)
- Confirmed: Balanced (already verified, importance matters more)

---

## Summary of Recommended Changes

### Priority 1 (Do First)
1. ✅ Reduce developing recency weight from 70% → 65%
2. ✅ Lengthen importance half-life from 120h → 168h
3. ✅ Reduce momentum penalty from -15% → -10%

### Priority 2 (Do After Testing Priority 1)
4. ⚠️ Smooth recency brackets (logarithmic instead of stepped)
5. ⚠️ Integrate conflicts into main ranking system

### Priority 3 (Nice to Have)
6. 🔵 Fix conflicts pagination
7. 🔵 Optimize two-pass ranking to single pass
8. 🔵 Make diversity bonus additive

---

## Data-Driven Decisions Needed

To optimize further, you would need to collect:

1. **User Behavior Data:**
   - Which articles users click on
   - Dwell time (how long they read)
   - Scroll depth (do they look at top 3 or top 20?)

2. **Satisfaction Metrics:**
   - Bounce rate (percentage leaving immediately)
   - Session length (time spent on site)
   - Return rate (do they come back?)

3. **Content Metadata:**
   - How often does category distribution change?
   - How many articles does a story get in first 24h vs 48h?
   - What's typical importance score by category?

**Current System:** Heuristic-based (expert-designed weights)
**Could Become:** Data-driven (optimize based on user engagement)

---

## Conclusion

Your ranking system is **sophisticated and well-thought-out**, but has three main issues:

1. **Recency weight is too aggressive** (especially at 70% for developing)
2. **Importance decay is too steep** (5-day half-life is too short)
3. **Conflicts uses completely different system** (creates inconsistency)

These three issues combine to make **old important stories disappear too quickly**. The recommended quick wins (reduce recency, lengthen decay, reduce penalty) should significantly improve the balance between freshness and importance.

Implementing the Priority 1 changes should take **<1 hour** and will noticeably improve ranking quality without major refactoring.
