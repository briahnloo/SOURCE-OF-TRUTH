"""Fact-check analytics service

Calculates error rates and statistics for sources based on fact-check results.
"""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import Article


def calculate_source_error_rates(db: Session, days: int = 30) -> List[Dict]:
    """
    Calculate error rates and composite impact scores for each source.
    
    Uses a composite "impact score" = flagged_count * (error_rate * 100)
    This balances both volume and rate to identify truly problematic sources.
    
    Args:
        db: Database session
        days: Number of days to look back (default: 30)
        
    Returns:
        Top 5 sources with highest fact-check impact scores (min 2 flagged, 2% error rate)
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get all articles from time window
    articles = db.query(Article).filter(Article.timestamp >= cutoff).all()
    
    # Group by source
    source_stats = {}
    
    for article in articles:
        if article.source not in source_stats:
            source_stats[article.source] = {
                'domain': article.source,
                'total_articles': 0,
                'flagged_count': 0,
                'false_count': 0,
                'disputed_count': 0,
            }
        
        stats = source_stats[article.source]
        stats['total_articles'] += 1
        
        if article.fact_check_status in ['false', 'disputed']:
            stats['flagged_count'] += 1
            
            if article.fact_check_status == 'false':
                stats['false_count'] += 1
            elif article.fact_check_status == 'disputed':
                stats['disputed_count'] += 1
    
    # Calculate error rates and composite impact scores
    result = []
    for source, stats in source_stats.items():
        if stats['total_articles'] > 0:
            stats['error_rate'] = stats['flagged_count'] / stats['total_articles']
            # Composite impact score: balances volume and rate
            # Higher score = more problematic source
            stats['impact_score'] = stats['flagged_count'] * (stats['error_rate'] * 100)
            result.append(stats)
    
    # Filter: minimum thresholds for fairness (≥2 flagged AND ≥2% error rate)
    result = [s for s in result if s['flagged_count'] >= 2 and s['error_rate'] >= 0.02]
    
    # Sort by composite impact score (highest first)
    result.sort(key=lambda x: x['impact_score'], reverse=True)
    
    # Return top 5 sources with highest impact
    return result[:5]


def get_flagged_summary(db: Session, days: int = 30) -> Dict[str, int]:
    """
    Get summary statistics of flagged articles.
    
    Args:
        db: Database session
        days: Number of days to look back
        
    Returns:
        Dict with false, disputed, total_flagged, total_checked counts
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Count by status
    articles = db.query(Article).filter(Article.timestamp >= cutoff).all()
    
    false_count = sum(1 for a in articles if a.fact_check_status == 'false')
    disputed_count = sum(1 for a in articles if a.fact_check_status == 'disputed')
    total_checked = sum(1 for a in articles if a.fact_check_status is not None)
    total_flagged = false_count + disputed_count
    
    return {
        'false': false_count,
        'disputed': disputed_count,
        'total_flagged': total_flagged,
        'total_checked': total_checked,
    }

