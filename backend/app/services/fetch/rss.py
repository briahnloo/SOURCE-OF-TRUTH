"""RSS/Atom feed fetcher"""

from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import feedparser

# RSS feed URLs
RSS_FEEDS = [
    # Wire services
    "https://feeds.apnews.com/rss/apf-topnews",
    "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    # International broadcasters
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.dw.com/xml/rss-en-world",
    "https://www.france24.com/en/rss",
    # National outlets
    "https://www.theguardian.com/world/rss",
    "https://feeds.npr.org/1004/rss.xml",
    "http://rss.cnn.com/rss/cnn_world.rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    # Additional outlets
    "https://www.economist.com/the-world-this-week/rss.xml",
    "https://www.independent.co.uk/news/world/rss",
]


def fetch_rss_articles() -> List[Dict[str, Any]]:
    """
    Fetch articles from all RSS feeds.

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp, summary
    """
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            # Extract domain from feed URL as source
            try:
                source = urlparse(feed_url).netloc
                # Clean up www. prefix
                if source.startswith("www."):
                    source = source[4:]
            except:
                source = "unknown"

            for entry in feed.entries[:50]:  # Limit to 50 per feed
                # Parse published date
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    timestamp = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    timestamp = datetime(*entry.updated_parsed[:6])
                else:
                    timestamp = datetime.utcnow()

                # Get summary
                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary[:500]  # Limit length
                elif hasattr(entry, "description"):
                    summary = entry.description[:500]

                articles.append(
                    {
                        "title": entry.title.strip(),
                        "url": entry.link,
                        "source": source,
                        "timestamp": timestamp,
                        "summary": summary,
                    }
                )

        except Exception as e:
            print(f"❌ RSS feed error ({feed_url}): {e}")
            continue

    print(f"✅ RSS: Fetched {len(articles)} articles from {len(RSS_FEEDS)} feeds")
    return articles
