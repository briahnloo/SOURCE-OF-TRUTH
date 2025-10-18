"""NGO and Government data source fetchers"""

from datetime import datetime
from typing import Any, Dict, List

import feedparser
import requests


def fetch_reliefweb() -> List[Dict[str, Any]]:
    """Fetch humanitarian reports from ReliefWeb API"""
    articles = []

    try:
        url = "https://api.reliefweb.int/v1/reports"
        params = {
            "appname": "truthlayer",
            "limit": 50,
            "sort": ["date:desc"],
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        if "data" in data:
            for item in data["data"]:
                fields = item.get("fields", {})

                # Parse date
                date_str = fields.get("date", {}).get("created", "")
                try:
                    timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()

                articles.append(
                    {
                        "title": fields.get("title", "").strip(),
                        "url": fields.get("url", ""),
                        "source": "reliefweb.int",
                        "timestamp": timestamp,
                        "summary": fields.get("body", "")[:500],
                    }
                )

        print(f"✅ ReliefWeb: Fetched {len(articles)} reports")

    except Exception as e:
        print(f"❌ ReliefWeb fetch error: {e}")

    return articles


def fetch_usgs_earthquakes() -> List[Dict[str, Any]]:
    """Fetch real-time earthquake data from USGS"""
    articles = []

    try:
        # All earthquakes in the past hour
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        if "features" in data:
            for feature in data["features"]:
                props = feature.get("properties", {})

                # Only include significant quakes (magnitude >= 4.0)
                magnitude = props.get("mag", 0)
                if magnitude < 4.0:
                    continue

                # Parse timestamp (Unix milliseconds)
                timestamp_ms = props.get("time", 0)
                timestamp = datetime.utcfromtimestamp(timestamp_ms / 1000)

                # Build title
                place = props.get("place", "Unknown location")
                title = f"Magnitude {magnitude:.1f} earthquake - {place}"

                articles.append(
                    {
                        "title": title,
                        "url": props.get("url", ""),
                        "source": "usgs.gov",
                        "timestamp": timestamp,
                        "summary": f"Earthquake details: {props.get('type', 'earthquake')} at depth {props.get('depth', 0):.1f} km",
                    }
                )

        print(f"✅ USGS: Fetched {len(articles)} earthquake events")

    except Exception as e:
        print(f"❌ USGS fetch error: {e}")

    return articles


def fetch_who_don() -> List[Dict[str, Any]]:
    """Fetch WHO Disease Outbreak News"""
    articles = []

    try:
        url = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"

        feed = feedparser.parse(url)

        for entry in feed.entries[:50]:
            # Parse published date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                timestamp = datetime(*entry.published_parsed[:6])
            else:
                timestamp = datetime.utcnow()

            # Get summary
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:500]

            articles.append(
                {
                    "title": entry.title.strip(),
                    "url": entry.link,
                    "source": "who.int",
                    "timestamp": timestamp,
                    "summary": summary,
                }
            )

        print(f"✅ WHO DON: Fetched {len(articles)} outbreak alerts")

    except Exception as e:
        print(f"❌ WHO DON fetch error: {e}")

    return articles


def fetch_nasa_firms() -> List[Dict[str, Any]]:
    """
    Fetch NASA FIRMS wildfire alerts.
    Note: Requires free MAP_KEY from https://firms.modaps.eosdis.nasa.gov/api/
    """
    articles = []

    # For MVP, we'll skip this since it requires registration
    # In production, add MAP_KEY to settings
    print("ℹ️  NASA FIRMS: Skipped (requires MAP_KEY registration)")

    # Example implementation (commented out):
    # try:
    #     map_key = "YOUR_MAP_KEY"
    #     url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/world/1"
    #
    #     response = requests.get(url, timeout=15)
    #     response.raise_for_status()
    #
    #     # Parse CSV
    #     import csv
    #     from io import StringIO
    #
    #     reader = csv.DictReader(StringIO(response.text))
    #     for row in reader:
    #         timestamp = datetime.strptime(row["acq_date"] + " " + row["acq_time"], "%Y-%m-%d %H%M")
    #
    #         articles.append({
    #             "title": f"Active fire detected at {row['latitude']}, {row['longitude']}",
    #             "url": f"https://firms.modaps.eosdis.nasa.gov/",
    #             "source": "nasa.gov",
    #             "timestamp": timestamp,
    #             "summary": f"Brightness: {row['bright_ti4']}K, Confidence: {row['confidence']}",
    #         })
    #
    #     print(f"✅ NASA FIRMS: Fetched {len(articles)} fire alerts")
    # except Exception as e:
    #     print(f"❌ NASA FIRMS fetch error: {e}")

    return articles


def fetch_un_ocha() -> List[Dict[str, Any]]:
    """Fetch UN OCHA humanitarian data"""
    articles = []

    try:
        # HDX (Humanitarian Data Exchange) API
        url = "https://data.humdata.org/api/3/action/package_search"
        params = {
            "q": "crisis OR conflict OR disaster",
            "rows": 20,
            "sort": "metadata_modified desc",
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get("success") and "result" in data:
            for package in data["result"].get("results", []):
                # Parse timestamp
                updated = package.get("metadata_modified", "")
                try:
                    timestamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()

                # Get location
                location = ", ".join([g.get("display_name", "") for g in package.get("groups", [])])

                title = package.get("title", "").strip()
                if location:
                    title = f"{title} - {location}"

                articles.append(
                    {
                        "title": title,
                        "url": f"https://data.humdata.org/dataset/{package.get('name', '')}",
                        "source": "unocha.org",
                        "timestamp": timestamp,
                        "summary": package.get("notes", "")[:500],
                    }
                )

        print(f"✅ UN OCHA: Fetched {len(articles)} humanitarian datasets")

    except Exception as e:
        print(f"❌ UN OCHA fetch error: {e}")

    return articles


def fetch_all_ngo_gov() -> List[Dict[str, Any]]:
    """Fetch from all NGO/Gov sources"""
    articles = []

    articles.extend(fetch_reliefweb())
    articles.extend(fetch_usgs_earthquakes())
    articles.extend(fetch_who_don())
    articles.extend(fetch_nasa_firms())
    articles.extend(fetch_un_ocha())

    return articles
