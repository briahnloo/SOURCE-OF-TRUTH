"""
Tests for conflict explanation generation
"""

import json
import numpy as np
import pytest

# Try to import the coherence module
try:
    from app.services.coherence import (
        calculate_narrative_coherence,
        identify_narrative_perspectives,
        generate_conflict_explanation,
        NarrativePerspective,
        ConflictExplanation,
    )

    COHERENCE_AVAILABLE = True
except ImportError:
    COHERENCE_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Requires full app environment")


# Mock Article class for testing
class MockArticle:
    def __init__(self, title, source, entities=None, summary=""):
        self.title = title
        self.source = source
        self.url = f"http://{source}/article"
        self.timestamp = "2024-01-01"
        self.summary = summary
        self.entities_json = json.dumps(entities) if entities else None


def create_mock_article(
    title: str, source: str, entities: list = None, summary: str = ""
) -> MockArticle:
    """Helper to create mock article"""
    return MockArticle(title, source, entities, summary)


def test_narrative_perspectives_clustering():
    """Test that articles are clustered into narrative perspectives"""
    # Create articles with different narratives
    articles = [
        create_mock_article(
            "Stampede at funeral causes dozens of injuries",
            "bbc.com",
            ["stampede", "injuries", "funeral"],
        ),
        create_mock_article(
            "Funeral chaos leads to multiple casualties",
            "france24.com",
            ["casualties", "chaos", "funeral"],
        ),
        create_mock_article(
            "Thousands mourn beloved leader at historic funeral",
            "aljazeera.com",
            ["mourning", "leader", "funeral"],
        ),
        create_mock_article(
            "Massive crowds gather to pay respects to political icon",
            "theguardian.com",
            ["crowds", "respects", "political"],
        ),
    ]

    # Create simple embeddings (simulating different narrative clusters)
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],  # Negative/tragedy focus
            [0.9, 0.1, 0.0],  # Negative/tragedy focus
            [0.0, 1.0, 0.0],  # Positive/celebration focus
            [0.0, 0.9, 0.1],  # Positive/celebration focus
        ]
    )

    # Identify perspectives
    perspectives = identify_narrative_perspectives(articles, embeddings)

    # Should have at least 2 perspectives
    assert len(perspectives) >= 2
    assert all(isinstance(p, NarrativePerspective) for p in perspectives)

    # Each perspective should have sources and titles
    for perspective in perspectives:
        assert len(perspective.sources) > 0
        assert len(perspective.representative_title) > 0
        assert perspective.article_count > 0
        assert perspective.sentiment in ["negative", "neutral", "positive"]


def test_conflict_explanation_generation():
    """Test that conflict explanation is generated properly"""
    # Create mock perspectives
    perspectives = [
        NarrativePerspective(
            sources=["bbc.com", "france24.com"],
            article_count=2,
            representative_title="Stampede at funeral causes dozens of injuries",
            key_entities=["stampede", "injuries", "casualties"],
            sentiment="negative",
            focus_keywords=["stampede", "chaos", "injuries"],
        ),
        NarrativePerspective(
            sources=["aljazeera.com", "theguardian.com"],
            article_count=2,
            representative_title="Thousands mourn beloved leader at historic funeral",
            key_entities=["mourning", "leader", "crowds"],
            sentiment="neutral",
            focus_keywords=["mourn", "beloved", "crowds"],
        ),
    ]

    # Generate explanation
    explanation = generate_conflict_explanation(perspectives)

    # Verify structure
    assert isinstance(explanation, ConflictExplanation)
    assert len(explanation.perspectives) == 2
    assert explanation.difference_type in ["facts", "emphasis", "framing", "interpretation"]
    assert len(explanation.key_difference) > 0


def test_calculate_narrative_coherence_with_conflict():
    """Test that coherence calculation returns explanation for conflicts"""
    # Create articles with conflicting narratives
    articles = [
        create_mock_article(
            "Death toll rises to 50 in bombing",
            "source1.com",
            ["bombing", "deaths", "casualties"],
        ),
        create_mock_article(
            "Explosion at market, casualties unknown",
            "source2.com",
            ["explosion", "market"],
        ),
    ]

    # Embeddings showing low similarity (conflict)
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])

    # Calculate coherence
    coherence, severity, explanation = calculate_narrative_coherence(articles, embeddings)

    # Should detect conflict
    assert coherence < 80  # Low coherence
    assert severity in ["low", "medium", "high"]  # Some level of conflict

    # Should generate explanation for conflict
    if severity != "none":
        assert explanation is not None
        assert isinstance(explanation, ConflictExplanation)
        assert len(explanation.perspectives) > 0


def test_calculate_narrative_coherence_no_conflict():
    """Test that coherence calculation doesn't generate explanation when no conflict"""
    # Create articles with similar narratives
    articles = [
        create_mock_article(
            "President announces new policy",
            "source1.com",
            ["president", "policy"],
        ),
        create_mock_article(
            "New policy announced by president",
            "source2.com",
            ["policy", "president"],
        ),
    ]

    # Embeddings showing high similarity (no conflict)
    embeddings = np.array([[1.0, 0.9], [0.9, 1.0]])

    # Calculate coherence
    coherence, severity, explanation = calculate_narrative_coherence(articles, embeddings)

    # Should not detect conflict
    assert coherence >= 60  # High coherence
    assert severity == "none" or severity == "low"

    # Should not generate explanation when no significant conflict
    if severity == "none":
        assert explanation is None


def test_serialization_to_json():
    """Test that ConflictExplanation can be serialized to JSON"""
    from dataclasses import asdict

    perspective = NarrativePerspective(
        sources=["bbc.com"],
        article_count=1,
        representative_title="Test Title",
        key_entities=["entity1", "entity2"],
        sentiment="neutral",
        focus_keywords=["keyword1", "keyword2"],
    )

    explanation = ConflictExplanation(
        perspectives=[asdict(perspective)],
        key_difference="Test difference",
        difference_type="emphasis",
    )

    # Should be serializable
    explanation_dict = asdict(explanation)
    json_str = json.dumps(explanation_dict)

    # Should be deserializable
    parsed = json.loads(json_str)
    assert parsed["key_difference"] == "Test difference"
    assert parsed["difference_type"] == "emphasis"
    assert len(parsed["perspectives"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

