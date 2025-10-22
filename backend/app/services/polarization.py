"""Polarization analytics service

Analyzes news sources for political polarization based on:
- Political extremity (distance from center on left/right spectrum)
- Sensational tone vs factual reporting

Provides rankings and sample excerpts showing polarizing rhetoric.
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Article
from app.services.bias import BiasScore, BiasAnalyzer


# Polarization keyword dictionaries with weighted scoring
POLARIZATION_KEYWORDS = {
    # High intensity inflammatory words (3 points each)
    'high': [
        'illegal', 'radical', 'threatens', 'racist', 'unfit', 'crazy', 
        'extortion', 'outraged', 'disgusted', 'scandal', 'corrupt', 
        'disaster', 'catastrophe', 'crisis', 'fraud', 'lie', 'liar',
        'betrayal', 'treason', 'extremist', 'fascist', 'communist',
        'destroyed', 'destroying', 'attacks', 'attack', 'war on',
        'alarming', 'shocking', 'explosive', 'bombshell'
    ],
    # Medium intensity charged words (2 points each)
    'medium': [
        'controversial', 'criticism', 'slams', 'blasts', 'demands',
        'accuses', 'condemns', 'rejects', 'refuses', 'defies',
        'targets', 'undermines', 'threatens', 'warns', 'fails',
        'struggling', 'backlash', 'outrage', 'anger', 'fury',
        'divided', 'clash', 'fight', 'battle', 'defeat'
    ],
    # Low intensity opinion words (1 point each)
    'low': [
        'questions', 'concerns', 'challenges', 'debate', 'divides',
        'dispute', 'disagrees', 'opposes', 'criticizes', 'doubt',
        'uncertain', 'unclear', 'controversial', 'contentious'
    ]
}

# Political keywords to identify political content
POLITICAL_KEYWORDS = [
    'trump', 'biden', 'democrat', 'republican', 'congress', 'senate',
    'house', 'president', 'administration', 'policy', 'bill', 'law',
    'election', 'campaign', 'governor', 'mayor', 'politician',
    'political', 'vote', 'voter', 'legislation', 'cabinet', 'white house',
    'impeach', 'appoint', 'executive order', 'veto', 'filibuster'
]

# Non-political keywords to exclude
EXCLUDE_KEYWORDS = {
    'sports': ['nfl', 'nba', 'mlb', 'nhl', 'game', 'player', 'team', 'score', 
               'playoff', 'season', 'coach', 'draft', 'trade', 'espn',
               'championship', 'super bowl', 'world series', 'stanley cup'],
    'entertainment': ['actor', 'actress', 'movie', 'film', 'show', 'celebrity',
                     'hollywood', 'series', 'netflix', 'streaming', 'album',
                     'song', 'concert', 'grammy', 'oscar', 'emmy']
}


def calculate_polarization_score(bias: BiasScore) -> float:
    """Calculate polarization score from bias metrics.
    
    Formula: (Political Extremity × 0.6) + (Sensationalism × 0.4)
    
    Political Extremity measures distance from political center (0-1):
    - Pure center (0.33, 0.34, 0.33) = 0
    - Far left (0.9, 0.1, 0) = high extremity
    - Far right (0, 0.1, 0.9) = high extremity
    
    Sensationalism is directly from tone.sensational (0-1)
    
    Args:
        bias: BiasScore object with political and tone dimensions
        
    Returns:
        Polarization score (0-100)
    """
    # Calculate political extremity (distance from center)
    # We measure how far left or right the source leans
    left = bias.political.get('left', 0.33)
    center = bias.political.get('center', 0.34)
    right = bias.political.get('right', 0.33)
    
    # Extremity = deviation from balanced (0.33, 0.34, 0.33)
    # Higher left OR right = more extreme
    political_extremity = abs(left - 0.33) + abs(right - 0.33)
    # Normalize to 0-1 range (max possible is ~1.34, so divide by 1.4)
    political_extremity = min(political_extremity / 1.4, 1.0)
    
    # Get sensationalism (0-1)
    sensationalism = bias.tone.get('sensational', 0.5)
    
    # Weighted combination: 60% political extremity, 40% sensationalism
    polarization = (political_extremity * 0.6) + (sensationalism * 0.4)
    
    # Scale to 0-100
    return round(polarization * 100, 2)


def is_political_content(title: str, summary: str = '') -> bool:
    """Check if article content is political (not sports/entertainment).
    
    Args:
        title: Article title
        summary: Article summary (optional)
        
    Returns:
        True if content is political, False otherwise
    """
    text = (title + ' ' + (summary or '')).lower()
    
    # Exclude sports content
    for keyword in EXCLUDE_KEYWORDS['sports']:
        if keyword in text:
            return False
    
    # Exclude entertainment content
    for keyword in EXCLUDE_KEYWORDS['entertainment']:
        if keyword in text:
            return False
    
    # Require at least one political keyword
    for keyword in POLITICAL_KEYWORDS:
        if keyword in text:
            return True
    
    return False


def score_excerpt_polarization(title: str, summary: str = '') -> Tuple[float, List[str]]:
    """Score how polarizing an excerpt is based on keyword analysis.
    
    Analyzes title and summary for:
    - Inflammatory keywords (weighted by intensity)
    - Emotional punctuation (exclamation marks)
    - ALL CAPS words
    - Quoted inflammatory phrases
    
    Args:
        title: Article title (primary source of polarization)
        summary: Article summary (secondary)
        
    Returns:
        Tuple of (polarization_score 0-100, list of found keywords)
    """
    text = (title + ' ' + (summary or '')).lower()
    score = 0
    found_keywords = []
    
    # Check for high intensity keywords (3 points each)
    for keyword in POLARIZATION_KEYWORDS['high']:
        if keyword in text:
            score += 3
            found_keywords.append(keyword)
    
    # Check for medium intensity keywords (2 points each)
    for keyword in POLARIZATION_KEYWORDS['medium']:
        if keyword in text:
            score += 2
            found_keywords.append(keyword)
    
    # Check for low intensity keywords (1 point each)
    for keyword in POLARIZATION_KEYWORDS['low']:
        if keyword in text:
            score += 1
            found_keywords.append(keyword)
    
    # Bonus for emotional punctuation
    exclamation_count = title.count('!')
    score += exclamation_count * 2
    
    # Bonus for ALL CAPS words (indicates shouting/emphasis)
    caps_words = re.findall(r'\b[A-Z]{3,}\b', title)
    score += len(caps_words) * 2
    
    # Bonus for quoted inflammatory content
    quotes = re.findall(r"['\"]([^'\"]+)['\"]", title)
    for quote in quotes:
        quote_lower = quote.lower()
        for keyword in POLARIZATION_KEYWORDS['high']:
            if keyword in quote_lower:
                score += 2  # Extra points for quoted inflammatory words
                break
    
    # Normalize to 0-100 scale
    # Max realistic score is around 30-40 for very polarizing content
    normalized_score = min((score / 0.4), 100)
    
    return round(normalized_score, 2), found_keywords


def get_polarizing_excerpts(source: str, db: Session, limit: int = 3) -> List[Dict]:
    """Get most polarizing article excerpts from a source.
    
    Analyzes articles to find the most inflammatory/polarizing content
    using keyword scoring. Prioritizes titles (headlines are designed
    to be polarizing) and filters for political content only.
    
    Args:
        source: Source domain to get excerpts from
        db: Database session
        limit: Maximum number of excerpts to return
        
    Returns:
        List of excerpt dicts with title, url, summary, timestamp,
        polarization_score, and highlighted_keywords
    """
    # Query recent articles from this source
    # Get more than needed to filter for political + polarizing content
    articles = (
        db.query(Article)
        .filter(Article.source == source)
        .order_by(Article.timestamp.desc())
        .limit(limit * 10)  # Get extra to filter for political content
        .all()
    )
    
    scored_excerpts = []
    
    for article in articles:
        # Filter: Only political content
        if not is_political_content(article.title, article.summary or ''):
            continue
        
        # Score the polarization of this excerpt
        polarization_score, keywords = score_excerpt_polarization(
            article.title, 
            article.summary or ''
        )
        
        # Extract topic tags (political keywords found)
        topic_tags = []
        title_lower = article.title.lower()
        for keyword in ['trump', 'biden', 'democrat', 'republican', 'congress', 'senate']:
            if keyword in title_lower:
                topic_tags.append(keyword.title())
        
        scored_excerpts.append({
            'title': article.title,
            'url': article.url,
            'summary': article.summary or '',
            'timestamp': article.timestamp,
            'polarization_score': polarization_score,
            'highlighted_keywords': keywords[:5],  # Top 5 keywords
            'topic_tags': topic_tags
        })
    
    # Sort by polarization score (highest first)
    scored_excerpts.sort(key=lambda x: x['polarization_score'], reverse=True)
    
    # Return top N most polarizing excerpts
    return scored_excerpts[:limit]


def calculate_source_polarization_rankings(
    db: Session, 
    min_articles: int = 10
) -> List[Dict]:
    """Calculate polarization rankings for all sources.
    
    For each source in bias metadata:
    1. Count articles in database
    2. Filter sources with sufficient article count
    3. Calculate polarization score
    4. Get sample excerpts
    5. Sort by polarization (highest to lowest)
    
    Args:
        db: Database session
        min_articles: Minimum article count to include source
        
    Returns:
        List of source dicts with polarization data, sorted by score (desc)
    """
    bias_analyzer = BiasAnalyzer()
    
    # Get article counts per source
    article_counts = dict(
        db.query(Article.source, func.count(Article.id))
        .group_by(Article.source)
        .all()
    )
    
    polarizing_sources = []
    
    # Analyze each source in bias metadata
    for domain, bias_data in bias_analyzer.metadata.items():
        # Check if we have enough articles from this source
        article_count = article_counts.get(domain, 0)
        if article_count < min_articles:
            continue
        
        # Create BiasScore object
        bias = BiasScore(
            geographic=bias_data.get('geographic', {}),
            political=bias_data.get('political', {}),
            tone=bias_data.get('tone', {}),
            detail=bias_data.get('detail', {})
        )
        
        # Calculate polarization score
        polarization_score = calculate_polarization_score(bias)
        
        # Get sample excerpts
        excerpts = get_polarizing_excerpts(domain, db, limit=3)
        
        polarizing_sources.append({
            'domain': domain,
            'polarization_score': polarization_score,
            'political_bias': bias.political,
            'tone_bias': bias.tone,
            'article_count': article_count,
            'sample_excerpts': excerpts
        })
    
    # Sort by polarization score (highest first)
    polarizing_sources.sort(key=lambda x: x['polarization_score'], reverse=True)
    
    return polarizing_sources

