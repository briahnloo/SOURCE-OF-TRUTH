"""NewsAPI fetcher (optional with API key)"""

from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from loguru import logger

from app.config import settings


def fetch_newsapi_articles() -> List[Dict[str, Any]]:
    """
    Fetch articles from NewsAPI (requires API key).

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp, summary
    """
    articles = []

    # Skip if no API key provided
    if not settings.newsapi_key:
        logger.debug("NewsAPI: Skipped (no API key)")
        return articles

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": settings.newsapi_key,
            "language": "en",
            "pageSize": 100,
            "category": "general",
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "ok" and "articles" in data:
            for article in data["articles"]:
                # Extract source
                source_name = article.get("source", {}).get("name", "unknown")

                # Try to get domain from URL
                try:
                    source = urlparse(article.get("url", "")).netloc
                    if source.startswith("www."):
                        source = source[4:]
                except:
                    source = source_name.lower().replace(" ", "")

                # Parse timestamp
                published_at = article.get("publishedAt", "")
                try:
                    timestamp = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()

                articles.append(
                    {
                        "title": article.get("title", "").strip(),
                        "url": article.get("url", ""),
                        "source": source,
                        "timestamp": timestamp,
                        "summary": article.get("description", "")[:500],
                    }
                )

        logger.info(f"✅ NewsAPI: Fetched {len(articles)} articles")

    except requests.RequestException as e:
        logger.warning(f"NewsAPI fetch error: {e}")
    except Exception as e:
        logger.warning(f"NewsAPI processing error: {e}")

    return articles
