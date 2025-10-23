"""International coverage analysis service"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from collections import defaultdict

from app.models import Article, Event
from app.services.bias import BiasAnalyzer


@dataclass
class InternationalSource:
    """Represents an international news source"""
    domain: str
    country: str
    region: str
    political_bias: Dict[str, float]  # {"left": 0.3, "center": 0.5, "right": 0.2}
    article_count: int


@dataclass
class InternationalCoverage:
    """Analysis of international coverage for an event"""
    has_international: bool
    source_count: int
    sources: List[InternationalSource]
    regional_breakdown: Dict[str, int]  # {"Europe": 3, "Asia": 2}
    political_distribution: Dict[str, float]  # {"left": 0.4, "center": 0.5, "right": 0.1}
    differs_from_us: bool
    coverage_gap_score: float  # 0-1 scale of how different from US coverage


def analyze_international_coverage(event: Event, articles: List[Article]) -> Optional[InternationalCoverage]:
    """
    Analyze international coverage for an event.
    
    Args:
        event: Event object
        articles: List of articles associated with the event
        
    Returns:
        InternationalCoverage object or None if no international sources
    """
    # Filter for international articles (non-US sources)
    international_articles = [
        article for article in articles 
        if article.source_country and article.source_country != 'US'
    ]
    
    if not international_articles:
        return None
    
    # Group articles by source domain
    source_groups = defaultdict(list)
    for article in international_articles:
        source_groups[article.source].append(article)
    
    # Build international sources list
    sources = []
    regional_breakdown = defaultdict(int)
    political_distribution = defaultdict(float)
    
    for domain, domain_articles in source_groups.items():
        # Get country and region from first article
        first_article = domain_articles[0]
        country = first_article.source_country or 'Unknown'
        region = first_article.source_region or 'Unknown'
        
        # Get political bias metadata
        bias_analyzer = BiasAnalyzer()
        bias_score = bias_analyzer.get_source_bias(domain)
        political_bias = bias_score.political if bias_score else {'left': 0.33, 'center': 0.34, 'right': 0.33}
        
        # Create international source
        source = InternationalSource(
            domain=domain,
            country=country,
            region=region,
            political_bias=political_bias,
            article_count=len(domain_articles)
        )
        sources.append(source)
        
        # Update regional breakdown
        regional_breakdown[region] += 1
        
        # Update political distribution (weighted by article count)
        weight = len(domain_articles)
        for bias_type, bias_value in political_bias.items():
            political_distribution[bias_type] += bias_value * weight
    
    # Normalize political distribution
    total_weight = sum(political_distribution.values())
    if total_weight > 0:
        for bias_type in political_distribution:
            political_distribution[bias_type] /= total_weight
    
    # Calculate coverage gap score (how different from US coverage)
    # For now, use a simple heuristic based on source diversity
    coverage_gap_score = min(1.0, len(sources) / 5.0)  # Max score at 5+ sources
    
    # Determine if coverage differs from US
    # This is a simplified check - in practice, you'd compare narrative angles
    differs_from_us = len(sources) >= 2 and coverage_gap_score > 0.3
    
    return InternationalCoverage(
        has_international=True,
        source_count=len(sources),
        sources=sources,
        regional_breakdown=dict(regional_breakdown),
        political_distribution=dict(political_distribution),
        differs_from_us=differs_from_us,
        coverage_gap_score=coverage_gap_score
    )


def store_international_coverage(event: Event, coverage: InternationalCoverage) -> None:
    """
    Store international coverage data in event.
    
    Args:
        event: Event object to update
        coverage: InternationalCoverage object to store
    """
    if coverage:
        # Convert to JSON-serializable format
        coverage_dict = asdict(coverage)
        event.international_coverage_json = json.dumps(coverage_dict)
    else:
        event.international_coverage_json = None


def load_international_coverage(event: Event) -> Optional[InternationalCoverage]:
    """
    Load international coverage data from event.
    
    Args:
        event: Event object with international_coverage_json
        
    Returns:
        InternationalCoverage object or None
    """
    if not event.international_coverage_json:
        return None
    
    try:
        coverage_dict = json.loads(event.international_coverage_json)
        
        # Convert sources back to InternationalSource objects
        sources = []
        for source_dict in coverage_dict.get('sources', []):
            source = InternationalSource(
                domain=source_dict['domain'],
                country=source_dict['country'],
                region=source_dict['region'],
                political_bias=source_dict['political_bias'],
                article_count=source_dict['article_count']
            )
            sources.append(source)
        
        return InternationalCoverage(
            has_international=coverage_dict['has_international'],
            source_count=coverage_dict['source_count'],
            sources=sources,
            regional_breakdown=coverage_dict['regional_breakdown'],
            political_distribution=coverage_dict['political_distribution'],
            differs_from_us=coverage_dict['differs_from_us'],
            coverage_gap_score=coverage_dict['coverage_gap_score']
        )
    except Exception as e:
        print(f"Error loading international coverage: {e}")
        return None