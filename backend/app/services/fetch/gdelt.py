"""GDELT data fetcher"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import quote

import requests


def fetch_gdelt_articles(minutes: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch recent articles from GDELT 2.0 Doc API.

    Args:
        minutes: Time window to fetch (default 15 minutes)

    Returns:
        List of article dictionaries with keys: title, url, source, timestamp
    """
    articles = []

    try:
        # GDELT Doc API endpoint
        # Query for recent articles with high relevance
        query = "sourcecountry:* AND language:english"

        # Time range
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=minutes)

        # Format: YYYYMMDDHHMMSS
        start_str = start_time.strftime("%Y%m%d%H%M%S")
        end_str = now.strftime("%Y%m%d%H%M%S")

        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={quote(query)}"
            f"&mode=artlist"
            f"&format=json"
            f"&maxrecords=250"
            f"&startdatetime={start_str}"
            f"&enddatetime={end_str}"
        )

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Handle empty response
        if not response.text or response.text.strip() == "":
            print("⚠️ GDELT: Empty response, skipping")
            return articles

        data = response.json()

        if "articles" in data:
            for article in data["articles"]:
                # Extract domain from URL
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(article.get("url", "")).netloc
                except:
                    domain = "unknown"

                articles.append(
                    {
                        "title": article.get("title", "").strip(),
                        "url": article.get("url", ""),
                        "source": domain,
                        "timestamp": datetime.strptime(
                            article.get("seendate", ""), "%Y%m%dT%H%M%SZ"
                        )
                        if "seendate" in article
                        else now,
                        "summary": article.get("socialimage", ""),  # GDELT doesn't provide summary
                    }
                )

        print(f"✅ GDELT: Fetched {len(articles)} articles")

    except requests.RequestException as e:
        print(f"⚠️ GDELT API error (skipping): {e}")
    except ValueError as e:
        print(f"⚠️ GDELT JSON parsing error (empty/invalid response): {e}")
    except Exception as e:
        print(f"⚠️ GDELT processing error (skipping): {e}")

    return articles
