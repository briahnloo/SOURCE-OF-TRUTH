"""
Backfill categories for existing events in the database.
Run this after the migration to categorize all existing events.
"""

import sqlite3
import json
from pathlib import Path
from typing import Tuple

# Get the database path
db_path = Path(__file__).parent.parent / "data" / "app.db"

def categorize_event_simple(summary: str, article_titles: list, sources: list) -> Tuple[str, float]:
    """Simple categorization based on keywords."""
    
    # Combine text for analysis
    text_combined = summary.lower()
    for title in article_titles[:5]:
        text_combined += " " + title.lower()
    
    # Check sources for official classifications
    sources_lower = [s.lower() for s in sources]
    
    # Natural disaster keywords and sources
    if any('usgs.gov' in s for s in sources_lower):
        return ('natural_disaster', 0.95)
    
    natural_disaster_keywords = [
        'earthquake', 'magnitude', 'tsunami', 'volcano', 'eruption',
        'hurricane', 'typhoon', 'cyclone', 'tornado', 'flood', 'wildfire',
        'avalanche', 'landslide', 'drought'
    ]
    natural_disaster_score = sum(1 for kw in natural_disaster_keywords if kw in text_combined)
    
    # Health/pandemic keywords and sources
    if any('who.int' in s for s in sources_lower):
        return ('health', 0.95)
    
    health_keywords = [
        'outbreak', 'epidemic', 'pandemic', 'disease', 'virus', 'vaccine',
        'covid', 'infection', 'who', 'cdc', 'health crisis'
    ]
    health_score = sum(1 for kw in health_keywords if kw in text_combined)
    
    # Politics keywords
    politics_keywords = [
        'trump', 'biden', 'president', 'congress', 'senate', 'house',
        'democrat', 'republican', 'election', 'vote', 'campaign', 'policy',
        'legislation', 'bill', 'law', 'government', 'administration',
        'white house', 'capitol', 'political', 'party', 'lawmakers',
        'prime minister', 'parliament', 'ceasefire', 'peace deal',
        'protest', 'rally', 'demonstration'
    ]
    politics_score = sum(1 for kw in politics_keywords if kw in text_combined)
    
    # International/conflict keywords
    international_keywords = [
        'israel', 'gaza', 'hamas', 'ukraine', 'russia', 'war', 'military',
        'strike', 'attack', 'conflict', 'troops', 'ceasefire', 'hostage',
        'nato', 'un security', 'diplomatic', 'sanctions', 'treaty'
    ]
    international_score = sum(1 for kw in international_keywords if kw in text_combined)
    
    # Crime keywords
    crime_keywords = [
        'murder', 'killed', 'shooting', 'robbery', 'theft', 'stolen',
        'arrested', 'police', 'investigation', 'suspect', 'heist',
        'criminal', 'prison', 'sentenced'
    ]
    crime_score = sum(1 for kw in crime_keywords if kw in text_combined)
    
    # Determine category based on scores
    scores = {
        'natural_disaster': natural_disaster_score,
        'health': health_score,
        'politics': politics_score,
        'international': international_score,
        'crime': crime_score
    }
    
    max_category = max(scores, key=scores.get)
    max_score = scores[max_category]
    
    # If no strong signal, classify as 'other'
    if max_score < 2:
        return ('other', 0.3)
    
    # Calculate confidence
    confidence = min(0.3 + (max_score * 0.1), 0.9)
    
    return (max_category, confidence)

def backfill_categories():
    """Categorize all events that don't have a category yet."""
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    print(f"🚀 Starting category backfill...\n")
    print(f"📊 Database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all events without a category
    cursor.execute("SELECT id, summary FROM events WHERE category IS NULL")
    events = cursor.fetchall()
    
    if not events:
        print("✅ All events already have categories!")
        conn.close()
        return
    
    print(f"📊 Found {len(events)} events to categorize...\n")
    
    categorized = 0
    for event_id, summary in events:
        try:
            # Get articles for this event
            cursor.execute("SELECT title, source FROM articles_raw WHERE cluster_id = ?", (event_id,))
            articles = cursor.fetchall()
            
            if not articles:
                continue
            
            titles = [a[0] for a in articles]
            sources = [a[1] for a in articles]
            
            # Categorize the event
            category, confidence = categorize_event_simple(summary, titles, sources)
            
            # Update the event
            cursor.execute(
                "UPDATE events SET category = ?, category_confidence = ? WHERE id = ?",
                (category, confidence, event_id)
            )
            
            categorized += 1
            
            if categorized % 10 == 0:
                print(f"✓ Categorized {categorized}/{len(events)} events...")
                conn.commit()
        
        except Exception as e:
            print(f"❌ Error categorizing event {event_id}: {e}")
            continue
    
    conn.commit()
    print(f"\n✅ Successfully categorized {categorized} events!")
    
    # Show category breakdown
    print("\n📈 Category breakdown:")
    for category in ['politics', 'international', 'natural_disaster', 'health', 'crime', 'other']:
        cursor.execute("SELECT COUNT(*) FROM events WHERE category = ?", (category,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   {category}: {count} events")
    
    conn.close()
    print(f"\n✨ Done! Database updated.")

if __name__ == "__main__":
    backfill_categories()
