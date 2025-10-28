"""RSS/Atom feed fetcher"""

from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import feedparser
from loguru import logger

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
    # International sources
    "https://www3.nhk.or.jp/nhkworld/en/news/rss.xml",  # NHK World (Japan)
    "https://www.abc.net.au/news/feed/51120/rss.xml",  # ABC Australia
    "https://www.cbc.ca/cmlink/rss-topstories",  # CBC Canada
    "https://www.euronews.com/rss?format=mrss",  # Euronews
    "https://www.africanews.com/feed/",  # Africanews
    "https://www.straitstimes.com/news/rss.xml",  # Straits Times (Singapore)
    # Conservative outlets
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://www.wsj.com/xml/rss/3_7085.xml",
    "https://www.dailywire.com/feeds/rss.xml",
    "https://www.nationalreview.com/feed/",
    "https://www.breitbart.com/feed/",
    "https://nypost.com/feed/",
    "https://www.washingtonexaminer.com/feed/",
    "https://thehill.com/feed/",
]


def fetch_rss_articles() -> List[Dict[str, Any]]:
    """
    Fetch articles from all RSS feeds with per-feed timeouts.

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp, summary
    """
    import threading
    articles = []

    def fetch_single_feed(feed_url: str, results: List[Dict[str, Any]]):
        """Fetch a single RSS feed with timeout protection"""
        try:
            # feedparser.parse() has no built-in timeout, use threading timeout
            feed = feedparser.parse(feed_url)

            # Check if parsing failed
            if not feed.entries:
                return

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

                results.append(
                    {
                        "title": entry.title.strip(),
                        "url": entry.link,
                        "source": source,
                        "timestamp": timestamp,
                        "summary": summary,
                    }
                )

        except Exception as e:
            logger.debug(f"RSS feed error ({feed_url}): {e}")

    # Fetch all feeds in parallel with timeout per feed (10 seconds)
    threads = []
    results_lock = threading.Lock()

    for feed_url in RSS_FEEDS:
        thread = threading.Thread(target=fetch_single_feed, args=(feed_url, articles), daemon=True)
        thread.start()
        threads.append((thread, feed_url))

    # Wait for all threads with timeout (10 seconds per feed, but process all in parallel)
    for thread, feed_url in threads:
        thread.join(timeout=10)
        if thread.is_alive():
            logger.debug(f"RSS feed timeout after 10s ({feed_url})")

    logger.info(f"✅ RSS: Fetched {len(articles)} articles from {len(RSS_FEEDS)} feeds")
    return articles
