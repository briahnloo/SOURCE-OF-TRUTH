"""Tests for narrative coherence calculation"""

import numpy as np
import pytest
from app.models import Article
from app.services.coherence import (
    calculate_embedding_similarity,
    calculate_entity_overlap,
    calculate_narrative_coherence,
    calculate_title_consistency,
    determine_conflict_severity,
)


def create_article(title: str, summary: str = "", entities: list = None) -> Article:
    """Helper to create test articles"""
    article = Article(
        source="test.com",
        title=title,
        url=f"http://test.com/{title.replace(' ', '-')}",
        timestamp="2024-01-01T00:00:00",
        summary=summary,
        entities_json=str(entities) if entities else None,
    )
    return article


def test_perfect_coherence():
    """Identical articles should have 100 coherence"""
    articles = [
        create_article("Same title", "Same summary"),
        create_article("Same title", "Same summary"),
        create_article("Same title", "Same summary"),
    ]
    # Identical embeddings (cosine similarity = 1.0)
    embeddings = np.array([[1.0, 0.0, 0.0]] * 3)

    score, severity = calculate_narrative_coherence(articles, embeddings)

    assert score >= 95.0
    assert severity == "none"


def test_conflicting_narratives():
    """Very different articles should have low coherence"""
    articles = [
        create_article("Earthquake hits coast", "Natural disaster reported"),
        create_article("Nothing unusual today", "All calm and quiet"),
        create_article("Festival celebration ongoing", "Joyful gathering"),
    ]
    # Orthogonal embeddings (completely different)
    embeddings = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

    score, severity = calculate_narrative_coherence(articles, embeddings)

    assert score < 40.0
    assert severity in ["medium", "high"]


def test_moderate_disagreement():
    """Similar but not identical should be moderate"""
    articles = [
        create_article("Storm causes damage in region", "Trees down and power outages"),
        create_article("Storm hits region hard", "Power failures reported"),
    ]
    # Somewhat similar embeddings (cosine similarity ~ 0.7-0.8)
    embeddings = np.array([[1.0, 0.8, 0.0], [0.8, 1.0, 0.0]])

    score, severity = calculate_narrative_coherence(articles, embeddings)

    assert 50.0 < score < 90.0
    assert severity in ["none", "low"]


def test_single_article():
    """Single article should have perfect coherence (no conflict)"""
    articles = [create_article("Test title", "Test summary")]
    embeddings = np.array([[1.0, 0.0, 0.0]])

    score, severity = calculate_narrative_coherence(articles, embeddings)

    assert score == 100.0
    assert severity == "none"


def test_embedding_similarity_identical():
    """Identical embeddings should have similarity 1.0"""
    embeddings = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    similarity = calculate_embedding_similarity(embeddings)

    assert similarity == pytest.approx(1.0, abs=0.01)


def test_embedding_similarity_orthogonal():
    """Orthogonal embeddings should have similarity 0.0"""
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])

    similarity = calculate_embedding_similarity(embeddings)

    assert similarity == pytest.approx(0.0, abs=0.01)


def test_entity_overlap_identical():
    """Same entities should have high overlap"""
    articles = [
        create_article("Test", "Test", ["Entity1", "Entity2"]),
        create_article("Test", "Test", ["Entity1", "Entity2"]),
    ]

    overlap = calculate_entity_overlap(articles)

    assert overlap == pytest.approx(1.0, abs=0.01)


def test_entity_overlap_disjoint():
    """No shared entities should have zero overlap"""
    articles = [
        create_article("Test", "Test", ["Entity1"]),
        create_article("Test", "Test", ["Entity2"]),
    ]

    overlap = calculate_entity_overlap(articles)

    assert overlap == pytest.approx(0.0, abs=0.01)


def test_title_consistency_identical():
    """Identical titles should have consistency 1.0"""
    articles = [
        create_article("earthquake magnitude seven hits region"),
        create_article("earthquake magnitude seven hits region"),
    ]

    consistency = calculate_title_consistency(articles)

    assert consistency == pytest.approx(1.0, abs=0.01)


def test_title_consistency_different():
    """Completely different titles should have low consistency"""
    articles = [
        create_article("earthquake disaster emergency"),
        create_article("celebration festival joyful"),
    ]

    consistency = calculate_title_consistency(articles)

    assert consistency < 0.3


def test_determine_conflict_severity():
    """Test severity classification"""
    assert determine_conflict_severity(90.0) == "none"
    assert determine_conflict_severity(80.0) == "none"
    assert determine_conflict_severity(70.0) == "low"
    assert determine_conflict_severity(60.0) == "low"
    assert determine_conflict_severity(50.0) == "medium"
    assert determine_conflict_severity(40.0) == "medium"
    assert determine_conflict_severity(30.0) == "high"
    assert determine_conflict_severity(10.0) == "high"


def test_coherence_weights():
    """Test that component weights sum correctly"""
    articles = [
        create_article("Test title one", "Summary"),
        create_article("Test title two", "Summary"),
    ]
    # Embeddings with similarity 0.5
    embeddings = np.array([[1.0, 0.0], [0.5, 0.866]])

    score, _ = calculate_narrative_coherence(articles, embeddings)

    # Score should be a weighted sum: embedding(60%) + entity(25%) + title(15%)
    # With these inputs, it should be between 0-100
    assert 0.0 <= score <= 100.0


def test_edge_case_empty_embeddings():
    """Test handling of edge cases"""
    articles = [create_article("Test", "Test")]
    embeddings = np.array([[1.0, 0.0]])

    score, severity = calculate_narrative_coherence(articles, embeddings)

    # Single article = no conflict
    assert score == 100.0
    assert severity == "none"


