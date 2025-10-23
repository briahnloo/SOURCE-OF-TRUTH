"""Country and region mapping service for international source tracking"""

from typing import Optional


# Domain to ISO country code mapping
DOMAIN_TO_COUNTRY = {
    # US sources
    'nytimes.com': 'US',
    'cnn.com': 'US',
    'npr.org': 'US',
    'feeds.npr.org': 'US',
    'rss.cnn.com': 'US',
    'rss.nytimes.com': 'US',
    'washingtonpost.com': 'US',
    'feeds.washingtonpost.com': 'US',
    'wsj.com': 'US',
    'foxnews.com': 'US',
    'moxie.foxnews.com': 'US',
    'dailywire.com': 'US',
    'nationalreview.com': 'US',
    'breitbart.com': 'US',
    'nypost.com': 'US',
    'washingtonexaminer.com': 'US',
    'thehill.com': 'US',
    'apnews.com': 'US',
    'feeds.apnews.com': 'US',
    'reuters.com': 'US',
    'reutersagency.com': 'US',
    
    # UK sources
    'bbc.co.uk': 'GB',
    'feeds.bbci.co.uk': 'GB',
    'theguardian.com': 'GB',
    'independent.co.uk': 'GB',
    'economist.com': 'GB',
    
    # German sources
    'dw.com': 'DE',
    'rss.dw.com': 'DE',
    
    # French sources
    'france24.com': 'FR',
    
    # Middle East sources
    'aljazeera.com': 'QA',
    
    # Japanese sources
    'nhk.or.jp': 'JP',
    'www3.nhk.or.jp': 'JP',
    
    # Australian sources
    'abc.net.au': 'AU',
    
    # Canadian sources
    'cbc.ca': 'CA',
    
    # European sources
    'euronews.com': 'EU',
    
    # African sources
    'africanews.com': 'AF',
    
    # Singapore sources
    'straitstimes.com': 'SG',
    
    # Social media (default to US)
    'reddit.com': 'US',
    
    # Default for unknown domains
    'unknown': 'US'
}

# Country to region mapping
COUNTRY_TO_REGION = {
    'US': 'North America',
    'CA': 'North America',
    'GB': 'Europe',
    'DE': 'Europe',
    'FR': 'Europe',
    'EU': 'Europe',
    'QA': 'Middle East',
    'JP': 'Asia',
    'AU': 'Oceania',
    'SG': 'Asia',
    'AF': 'Africa'
}


def get_country_from_domain(domain: str) -> Optional[str]:
    """
    Map domain to ISO country code.
    
    Args:
        domain: Source domain (e.g., 'bbc.co.uk', 'cnn.com')
        
    Returns:
        ISO country code (e.g., 'GB', 'US') or None if not found
    """
    if not domain:
        return None
    
    # Clean domain (remove www, http, etc.)
    domain = domain.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]
    if domain.startswith('http://'):
        domain = domain[7:]
    if domain.startswith('https://'):
        domain = domain[8:]
    
    # Direct lookup
    if domain in DOMAIN_TO_COUNTRY:
        return DOMAIN_TO_COUNTRY[domain]
    
    # Try to match partial domains
    for known_domain, country in DOMAIN_TO_COUNTRY.items():
        if domain.endswith(known_domain) or known_domain in domain:
            return country
    
    # Default to US for unknown domains
    return 'US'


def get_region_from_country(country: str) -> Optional[str]:
    """
    Map country code to geographic region.
    
    Args:
        country: ISO country code (e.g., 'US', 'GB')
        
    Returns:
        Geographic region (e.g., 'North America', 'Europe') or None if not found
    """
    if not country:
        return None
    
    return COUNTRY_TO_REGION.get(country.upper())


def is_international_source(domain: str) -> bool:
    """
    Check if a source is international (non-US).
    
    Args:
        domain: Source domain
        
    Returns:
        True if source is international, False if US or unknown
    """
    country = get_country_from_domain(domain)
    return country is not None and country != 'US'


def get_source_metadata(domain: str) -> dict:
    """
    Get complete metadata for a source domain.
    
    Args:
        domain: Source domain
        
    Returns:
        Dictionary with country, region, and is_international
    """
    country = get_country_from_domain(domain)
    region = get_region_from_country(country) if country else None
    
    return {
        'country': country,
        'region': region,
        'is_international': country != 'US' if country else False
    }