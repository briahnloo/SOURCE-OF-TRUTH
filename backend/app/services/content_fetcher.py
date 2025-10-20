"""Article content fetching service

Extracts full article text from URLs using newspaper3k.
Handles paywalls, timeouts, and anti-scraping measures gracefully.
"""

from typing import Optional
try:
    import newspaper
    from newspaper import Article
except ImportError:
    from newspaper import Article
import requests
from loguru import logger


class ContentFetcher:
    """Fetches and extracts full article content from URLs"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize content fetcher.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    
    def fetch_article_text(self, url: str) -> Optional[str]:
        """
        Fetch and extract full article text from URL.
        
        Args:
            url: Article URL to fetch
            
        Returns:
            Extracted article text or None if fetch fails
        """
        try:
            # Create article object with configuration
            config = newspaper.Config()
            config.browser_user_agent = self.user_agent
            config.request_timeout = self.timeout
            
            article = Article(url, config=config)
            
            # Download and parse
            article.download()
            article.parse()
            
            # Get text content
            text = article.text
            
            if not text or len(text) < 100:
                logger.warning(f"Article too short or empty: {url}")
                return None
            
            logger.info(f"Successfully fetched {len(text)} chars from {url}")
            return text
            
        except newspaper.ArticleException as e:
            logger.warning(f"Newspaper error fetching {url}: {e}")
            return None
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching {url}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def is_paywall_detected(self, text: Optional[str]) -> bool:
        """
        Detect if content is behind a paywall or is just fundraising boilerplate.
        
        Args:
            text: Article text
            
        Returns:
            True if paywall/fundraising indicators detected
        """
        if not text:
            return False
        
        paywall_indicators = [
            "subscribe to continue reading",
            "create a free account",
            "this article is for subscribers",
            "please log in",
            "sign up to read",
            "subscriber exclusive",
            "your donation allows us",  # Fundraising pitch
            "choose not to lock",  # Independent-specific
            "believe quality journalism",  # Fundraising pitch
            "paid for by those who can afford it",  # Fundraising pitch
        ]
        
        text_lower = text.lower()
        has_paywall = any(indicator in text_lower for indicator in paywall_indicators)
        
        # Also check if content is suspiciously short and contains fundraising language
        if len(text) < 1000 and ("donation" in text_lower or "paywall" in text_lower):
            has_paywall = True
        
        return has_paywall
    
    def get_article_metadata(self, url: str) -> dict:
        """
        Extract article metadata (title, authors, publish date).
        
        Args:
            url: Article URL
            
        Returns:
            Dict with metadata fields
        """
        try:
            config = newspaper.Config()
            config.browser_user_agent = self.user_agent
            config.request_timeout = self.timeout
            
            article = Article(url, config=config)
            article.download()
            article.parse()
            
            return {
                'title': article.title,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'top_image': article.top_image,
                'text_length': len(article.text) if article.text else 0,
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return {}

