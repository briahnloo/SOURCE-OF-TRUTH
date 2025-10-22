"""Importance scoring service for news events"""

from datetime import datetime
from app.models import Event


def calculate_importance_score(event: Event) -> float:
    """
    Calculate importance score (0-100) based on multiple factors.
    
    Higher score = more important story
    
    Factors considered:
    1. Category weight (0-30 points) - international/politics get higher scores
    2. Conflict severity (0-15 points) - meaningful disagreements get priority
    3. Coverage intensity (0-20 points) - more articles/sources = bigger story
    4. Recency (0-10 points) - breaking news gets priority
    5. Truth score quality (0-10 points) - higher verification = more credible
    """
    score = 0.0
    
    # 1. Base category weight (0-30 points)
    category_weights = {
        'international': 30,  # Gaza, Ukraine, major conflicts
        'politics': 25,      # Domestic political events
        'natural_disaster': 20,  # Earthquakes, hurricanes, etc.
        'health': 20,        # Health crises, pandemics
        'crime': 15,         # Criminal events
        'other': 10          # Miscellaneous
    }
    score += category_weights.get(event.category, 10)
    
    # 2. Conflict severity (0-15 points)
    # Meaningful disagreements between sources get priority
    if event.has_conflict and event.coherence_score:
        if event.coherence_score < 40:
            score += 15  # High conflict - major disagreements
        elif event.coherence_score < 60:
            score += 10  # Medium conflict - significant differences
        elif event.coherence_score < 70:
            score += 5   # Low conflict - minor differences
    
    # 3. Coverage intensity (0-20 points)
    # More articles + sources = bigger story
    if event.articles_count >= 15:
        score += 10  # Major story
    elif event.articles_count >= 10:
        score += 7   # Significant story
    elif event.articles_count >= 6:
        score += 5   # Moderate story
    
    if event.unique_sources >= 10:
        score += 10  # High source diversity
    elif event.unique_sources >= 8:
        score += 7   # Good source diversity
    elif event.unique_sources >= 5:
        score += 5   # Moderate source diversity
    
    # 4. Recency (0-10 points)
    # Breaking news gets priority
    now = datetime.utcnow()
    hours_since = (now - event.last_seen).total_seconds() / 3600
    
    if hours_since <= 6:
        score += 10  # Very recent - breaking news
    elif hours_since <= 12:
        score += 7   # Recent - developing story
    elif hours_since <= 24:
        score += 4   # Yesterday - still relevant
    elif hours_since <= 48:
        score += 2   # Two days ago - aging
    
    # 5. Truth score quality (0-10 points)
    # Higher verification = more credible = more important
    if event.truth_score >= 75:
        score += 10  # Highly verified
    elif event.truth_score >= 65:
        score += 7   # Well verified
    elif event.truth_score >= 55:
        score += 5   # Moderately verified
    elif event.truth_score >= 45:
        score += 3   # Somewhat verified
    
    return min(score, 100.0)  # Cap at 100
