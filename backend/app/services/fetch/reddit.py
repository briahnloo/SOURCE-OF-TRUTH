"""Reddit JSON fetcher"""

from datetime import datetime
from typing import Any, Dict, List

import requests

SUBREDDITS = ["worldnews", "news"]


def fetch_reddit_articles() -> List[Dict[str, Any]]:
    """
    Fetch top posts from Reddit subreddits via JSON endpoint.

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp
    """
    articles = []

    headers = {"User-Agent": "TruthLayer/1.0 (News Aggregator)"}

    for subreddit in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}.json?limit=25"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "data" in data and "children" in data["data"]:
                for post in data["data"]["children"]:
                    post_data = post.get("data", {})

                    # Skip self-posts (text only)
                    if post_data.get("is_self", True):
                        continue

                    # Skip if no URL
                    post_url = post_data.get("url", "")
                    if not post_url or "reddit.com" in post_url:
                        continue

                    # Extract source from URL
                    try:
                        from urllib.parse import urlparse

                        source = urlparse(post_url).netloc
                        if source.startswith("www."):
                            source = source[4:]
                    except:
                        source = "reddit"

                    # Convert Unix timestamp
                    created_utc = post_data.get("created_utc", 0)
                    timestamp = datetime.utcfromtimestamp(created_utc)

                    articles.append(
                        {
                            "title": post_data.get("title", "").strip(),
                            "url": post_url,
                            "source": source,
                            "timestamp": timestamp,
                            "summary": post_data.get("selftext", "")[:200],
                        }
                    )

        except requests.RequestException as e:
            print(f"❌ Reddit fetch error (r/{subreddit}): {e}")
        except Exception as e:
            print(f"❌ Reddit processing error (r/{subreddit}): {e}")

    print(f"✅ Reddit: Fetched {len(articles)} posts from {len(SUBREDDITS)} subreddits")
    return articles
