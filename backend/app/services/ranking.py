"""Improved event ranking service balancing freshness, importance, and quality"""

import math
from datetime import datetime
from app.models import Event


def calculate_aged_importance(event: Event) -> float:
    """
    Apply time-decay to importance score.

    Importance starts high but naturally decays over time.
    This prevents old stories from dominating forever.

    Decay formula: importance_score × (1 - (hours_old / 240))
    - At 0 hours: full importance
    - At 120 hours (5 days): 50% of original importance
    - At 240 hours (10 days): fully decayed to baseline

    Args:
        event: Event to calculate aged importance for

    Returns:
        Aged importance score (0-100)
    """
    now = datetime.utcnow()
    hours_old = (now - event.last_seen).total_seconds() / 3600

    base_importance = event.importance_score or 0

    # Linear decay over 10 days (240 hours)
    decay_factor = max(0, 1 - (hours_old / 240))
    aged_importance = base_importance * decay_factor

    return aged_importance


def calculate_recency_score(event: Event) -> float:
    """
    Calculate recency score with aggressive exponential decay.

    Fresh events get high scores; older events decay exponentially.
    This ensures breaking news bubbles to top quickly.

    Time brackets:
    - 0-6h (fresh): 1.0 (breaking news)
    - 6-24h (same day): 0.85 (still relevant)
    - 24-48h (two days): 0.60 (aging)
    - 48-72h (three days): 0.35 (stale)
    - 72h+: exponential decay (0.1 × e^(-hours_old/240))

    Args:
        event: Event to calculate recency score for

    Returns:
        Recency score (0-1.0)
    """
    now = datetime.utcnow()
    hours_old = (now - event.last_seen).total_seconds() / 3600

    if hours_old <= 6:
        return 1.0  # Fresh breaking news
    elif hours_old <= 24:
        return 0.85  # Still very relevant
    elif hours_old <= 48:
        return 0.60  # Two days old - aging
    elif hours_old <= 72:
        return 0.35  # Three days - getting stale
    else:
        # Exponential decay: 0.1 × e^(-hours_old/240)
        # At day 7: ≈0.07, at day 14: ≈0.005
        return 0.1 * math.exp(-hours_old / 240)


def calculate_quality_score(event: Event) -> float:
    """
    Calculate quality score based on verification and source diversity.

    Higher truth_score and more sources = higher quality.

    Args:
        event: Event to calculate quality score for

    Returns:
        Quality score (0-1.0)
    """
    # Normalize truth score (0-100 → 0-1.0)
    truth_component = (event.truth_score or 0) / 100.0

    # Normalize source diversity (target: 5+ sources = full score)
    sources_component = min((event.unique_sources or 0) / 5.0, 1.0)

    # Average the two components
    quality = (truth_component * 0.6 + sources_component * 0.4)

    return quality


def calculate_diversity_bonus(event: Event, top_events: list, position: int) -> float:
    """
    Small bonus for events with different category than top 3.

    Prevents similar stories from clustering at top.
    Ensures users see variety in what appears first.

    Args:
        event: Event to evaluate
        top_events: List of current top events
        position: Position in current ranking

    Returns:
        Bonus factor (0.95-1.05)
    """
    if position > 3:
        return 1.0  # No bonus outside top 3

    if position == 0:
        return 1.0  # Top event, no bonus needed

    # Check if category differs from top event
    top_category = top_events[0].category if top_events else None
    if top_category and event.category != top_category:
        return 1.05  # 5% boost for category diversity

    return 1.0


def calculate_balanced_ranking_score(event: Event, position: int = 0, top_events: list = None) -> float:
    """
    Calculate final ranking score balancing:
    - 25% Importance (with time-decay)
    - 25% Quality (truth score + source diversity)
    - 50% Recency (aggressive time-based decay)

    Plus optional diversity bonus for variety.

    This formula ensures:
    1. Fresh events bubble to top quickly
    2. Quality events still rank high even if slightly older
    3. Old events naturally fade (no artificial manipulation)
    4. Variety in top events by category

    Args:
        event: Event to score
        position: Current position in ranking (for diversity bonus)
        top_events: List of current top events (for diversity bonus)

    Returns:
        Final ranking score (higher = better, typically 0-1.0+)
    """
    if top_events is None:
        top_events = []

    # Component weights (sum = 1.0)
    importance_weight = 0.25
    quality_weight = 0.25
    recency_weight = 0.50

    # Calculate components
    aged_importance = calculate_aged_importance(event)
    importance_normalized = (aged_importance or 0) / 100.0  # Normalize to 0-1.0

    quality = calculate_quality_score(event)
    recency = calculate_recency_score(event)

    # Combine with weights
    balanced_score = (
        importance_weight * importance_normalized +
        quality_weight * quality +
        recency_weight * recency
    )

    # Apply diversity bonus (small impact)
    diversity_bonus = calculate_diversity_bonus(event, top_events, position)
    final_score = balanced_score * diversity_bonus

    return final_score


def rank_events(events: list) -> list:
    """
    Rank events using the improved balanced ranking formula.

    This is the main entry point for ranking a list of events.

    Args:
        events: List of Event objects to rank

    Returns:
        Events sorted by ranking score (highest first)
    """
    # Score all events first pass (no diversity bonus yet)
    scored_events = []
    for event in events:
        score = calculate_balanced_ranking_score(event)
        scored_events.append((event, score))

    # Sort by score
    scored_events.sort(key=lambda x: x[1], reverse=True)

    # Get top events for diversity calculation
    top_events = [e[0] for e in scored_events[:5]]

    # Recalculate with diversity bonus for top positions
    final_scored = []
    for position, (event, _) in enumerate(scored_events):
        final_score = calculate_balanced_ranking_score(event, position, top_events)
        final_scored.append((event, final_score))

    # Re-sort with diversity bonus applied
    final_scored.sort(key=lambda x: x[1], reverse=True)

    return [e[0] for e in final_scored]
