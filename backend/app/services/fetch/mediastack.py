"""Mediastack API fetcher (optional with API key)"""

from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from app.config import settings


def fetch_mediastack_articles() -> List[Dict[str, Any]]:
    """
    Fetch articles from Mediastack API (requires API key).

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp, summary
    """
    articles = []

    # Skip if no API key provided
    if not settings.mediastack_key:
        print("ℹ️  Mediastack: Skipped (no API key)")
        return articles

    try:
        url = "http://api.mediastack.com/v1/news"
        params = {
            "access_key": settings.mediastack_key,
            "languages": "en",
            "limit": 100,
            "sort": "published_desc",
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        if "data" in data:
            for article in data["data"]:
                # Extract source
                source_name = article.get("source", "unknown")

                # Try to get domain from URL
                try:
                    source = urlparse(article.get("url", "")).netloc
                    if source.startswith("www."):
                        source = source[4:]
                except:
                    source = source_name.lower().replace(" ", "")

                # Parse timestamp
                published_at = article.get("published_at", "")
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

        print(f"✅ Mediastack: Fetched {len(articles)} articles")

    except requests.RequestException as e:
        print(f"❌ Mediastack fetch error: {e}")
    except Exception as e:
        print(f"❌ Mediastack processing error: {e}")

    return articles
