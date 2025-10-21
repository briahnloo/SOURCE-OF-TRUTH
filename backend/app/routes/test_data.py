"""Test data endpoints for development and Render free tier"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Article, Event

router = APIRouter()


@router.post("/test-data/populate")
async def populate_test_data(db: Session = Depends(get_db)):
    """Populate database with test events for demo purposes"""
    
    # Sample test events
    test_events = [
        {
            "summary": "Trump announces new infrastructure plan for 2024",
            "category": "politics",
            "articles_count": 8,
            "unique_sources": 6,
            "geo_diversity": 0.75,
            "coherence_score": 85.0,
            "truth_score": 65.0,
            "has_conflict": False,
            "underreported": False
        },
        {
            "summary": "Biden administration announces climate change initiatives",
            "category": "politics", 
            "articles_count": 12,
            "unique_sources": 8,
            "geo_diversity": 0.80,
            "coherence_score": 78.0,
            "truth_score": 70.0,
            "has_conflict": False,
            "underreported": False
        },
        {
            "summary": "Gaza ceasefire negotiations continue amid tensions",
            "category": "international",
            "articles_count": 15,
            "unique_sources": 10,
            "geo_diversity": 0.85,
            "coherence_score": 45.0,
            "truth_score": 60.0,
            "has_conflict": True,
            "underreported": False
        },
        {
            "summary": "Earthquake magnitude 6.2 strikes California",
            "category": "natural_disaster",
            "articles_count": 6,
            "unique_sources": 4,
            "geo_diversity": 0.60,
            "coherence_score": 92.0,
            "truth_score": 80.0,
            "has_conflict": False,
            "underreported": False
        },
        {
            "summary": "Tech layoffs continue as companies restructure",
            "category": "other",
            "articles_count": 9,
            "unique_sources": 7,
            "geo_diversity": 0.70,
            "coherence_score": 88.0,
            "truth_score": 62.0,
            "has_conflict": False,
            "underreported": False
        }
    ]
    
    created_events = []
    
    for event_data in test_events:
        # Create event
        event = Event(
            summary=event_data["summary"],
            category=event_data["category"],
            articles_count=event_data["articles_count"],
            unique_sources=event_data["unique_sources"],
            geo_diversity=event_data["geo_diversity"],
            coherence_score=event_data["coherence_score"],
            truth_score=event_data["truth_score"],
            has_conflict=event_data["has_conflict"],
            underreported=event_data["underreported"],
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        db.add(event)
        db.flush()  # Get the ID
        
        # Create sample articles for each event
        sample_sources = [
            "bbc.com", "reuters.com", "apnews.com", "npr.org", 
            "nytimes.com", "washingtonpost.com", "cnn.com", "foxnews.com"
        ]
        
        for i in range(event_data["articles_count"]):
            article = Article(
                source=sample_sources[i % len(sample_sources)],
                title=f"Sample article {i+1} for {event.summary[:30]}...",
                url=f"https://example.com/article-{event.id}-{i+1}",
                timestamp=datetime.utcnow(),
                language="en",
                summary=f"Sample summary for article {i+1}",
                text_snippet=f"Sample text snippet for article {i+1}",
                cluster_id=event.id
            )
            db.add(article)
        
        created_events.append(event)
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Created {len(created_events)} test events with sample articles",
        "events": [
            {
                "id": event.id,
                "summary": event.summary,
                "category": event.category,
                "truth_score": event.truth_score,
                "articles_count": event.articles_count
            }
            for event in created_events
        ]
    }


@router.delete("/test-data/clear")
async def clear_test_data(db: Session = Depends(get_db)):
    """Clear all test data from database"""
    
    # Delete all articles
    db.query(Article).delete()
    
    # Delete all events  
    db.query(Event).delete()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "All test data cleared"
    }
