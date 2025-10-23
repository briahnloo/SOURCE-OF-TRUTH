"""Conflict priority scoring for ranking conflicts page"""

from datetime import datetime
from app.models import Event


def calculate_conflict_priority(event: Event) -> float:
    """
    Calculate conflict priority score (0-100) specifically for the conflicts page.
    
    This ranks conflicts by how "pressing" and "newsworthy" they are, balancing:
    1. Conflict severity (40%) - How much do sources disagree?
    2. Issue importance (35%) - Category, coverage intensity
    3. Recency (25%) - Time decay for breaking news
    
    Higher score = more pressing conflict that should appear first
    
    Args:
        event: Event object with conflict data
        
    Returns:
        Float score between 0-100
    """
    score = 0.0
    
    # ============================================================
    # 1. CONFLICT SEVERITY (0-40 points)
    # ============================================================
    # Direct disagreement between sources is the PRIMARY factor
    # Lower coherence = higher severity = higher priority
    
    if event.coherence_score is not None:
        # Coherence ranges: 0-100 (0 = total disagreement, 100 = perfect agreement)
        # Invert so lower coherence = higher score
        coherence_normalized = 100 - event.coherence_score
        
        # Scale to 0-40 points with emphasis on severe conflicts
        if event.coherence_score < 30:
            # 30-40 points: EXTREME conflict (coherence 0-30)
            # These are major factual disputes - TOP PRIORITY
            score += 30 + (coherence_normalized / 100) * 10
        elif event.coherence_score < 50:
            # 20-30 points: HIGH conflict (coherence 30-50)
            # Significant disagreements on key facts/framing
            score += 20 + ((coherence_normalized - 70) / 20) * 10
        elif event.coherence_score < 70:
            # 10-20 points: MEDIUM conflict (coherence 50-70)
            # Notable differences in emphasis or interpretation
            score += 10 + ((coherence_normalized - 50) / 20) * 10
        else:
            # 0-10 points: LOW conflict (coherence 70-100)
            # Minor differences - these shouldn't appear much
            score += (coherence_normalized - 30) / 30 * 10
    
    # Bonus for having left AND right coverage (true political divide)
    # Parse conflict explanation to check
    if event.conflict_explanation_json:
        import json
        try:
            explanation = json.loads(event.conflict_explanation_json)
            perspectives = explanation.get('perspectives', [])
            political_leanings = set()
            for p in perspectives:
                if isinstance(p, dict) and p.get('political_leaning'):
                    political_leanings.add(p['political_leaning'])
            
            # +5 points if we have left AND right perspectives
            if 'left' in political_leanings and 'right' in political_leanings:
                score += 5
                
            # Additional +3 points if keyword overlap is LOW (perspectives say different things)
            keyword_overlap = explanation.get('keyword_overlap')
            if keyword_overlap is not None:
                if keyword_overlap < 0.25:  # <25% overlap = very different narratives
                    score += 3
                elif keyword_overlap < 0.35:  # 25-35% overlap = somewhat different
                    score += 1.5
        except (json.JSONDecodeError, AttributeError):
            pass
    
    # ============================================================
    # 2. ISSUE IMPORTANCE (0-35 points)
    # ============================================================
    # Breaking news about major issues gets priority
    
    # 2a. Category weight (0-15 points)
    category_weights = {
        'international': 15,  # Gaza, Ukraine, major global conflicts
        'politics': 12,       # US political events, policy debates
        'health': 10,         # Health crises, pandemics
        'natural_disaster': 10,  # Disasters, climate events
        'crime': 8,           # Major criminal events
        'other': 5            # Miscellaneous
    }
    score += category_weights.get(event.category, 5)
    
    # 2b. Coverage intensity (0-20 points)
    # More articles/sources = bigger, more important story
    coverage_score = 0
    
    # Article count component (0-10 points)
    if event.articles_count >= 20:
        coverage_score += 10  # Major story - extensive coverage
    elif event.articles_count >= 15:
        coverage_score += 8   # Significant story
    elif event.articles_count >= 10:
        coverage_score += 6   # Moderate-high coverage
    elif event.articles_count >= 6:
        coverage_score += 4   # Moderate coverage
    else:
        coverage_score += 2   # Limited coverage
    
    # Source diversity component (0-10 points)
    if event.unique_sources >= 10:
        coverage_score += 10  # Very high source diversity
    elif event.unique_sources >= 8:
        coverage_score += 8   # High source diversity
    elif event.unique_sources >= 6:
        coverage_score += 6   # Good source diversity
    elif event.unique_sources >= 4:
        coverage_score += 4   # Moderate source diversity
    else:
        coverage_score += 2   # Limited sources
    
    score += coverage_score
    
    # ============================================================
    # 3. RECENCY (0-35 points) - INCREASED from 25 to give novelty more weight
    # ============================================================
    # Time decay: breaking news gets priority, old news fades
    # IMPROVED: Increased recency weight to prevent old conflicts from dominating
    # even when they had high importance at the time of discovery

    now = datetime.utcnow()
    hours_since = (now - event.last_seen).total_seconds() / 3600

    if hours_since <= 4:
        score += 35  # Just happened - BREAKING NEWS (increased from 25)
    elif hours_since <= 8:
        score += 28  # Very recent - still breaking (increased from 20)
    elif hours_since <= 12:
        score += 22  # Recent - developing story (increased from 15)
    elif hours_since <= 24:
        score += 15  # Yesterday - still relevant (increased from 10)
    elif hours_since <= 48:
        score += 10  # Two days ago - aging but still current (increased from 6)
    elif hours_since <= 72:
        score += 5   # Three days ago - fading (increased from 3)
    else:
        # After 3 days, gradual decay but don't completely zero out
        # Important conflicts should still appear even if older
        # IMPROVED: Slower decay curve - new articles get better boost
        days_old = hours_since / 24
        decay_score = max(0.5, 5 - (days_old - 3) * 0.2)  # Slower decay (was 0.3)
        score += decay_score
    
    return min(score, 100.0)  # Cap at 100


def get_conflict_severity_label(coherence_score: float) -> str:
    """
    Get human-readable label for conflict severity.
    
    Args:
        coherence_score: Coherence score (0-100)
        
    Returns:
        Severity label string
    """
    if coherence_score < 30:
        return "extreme"
    elif coherence_score < 50:
        return "high"
    elif coherence_score < 70:
        return "medium"
    else:
        return "low"

