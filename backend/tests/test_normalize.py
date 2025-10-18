"""Tests for normalization and deduplication logic"""

import pytest
from app.services.normalize import (
    calculate_title_similarity,
    detect_language,
    normalize_url,
)


def test_detect_language_english():
    """Test English language detection"""
    text = "This is an English text with many words"
    assert detect_language(text) == "en"


def test_detect_language_non_english():
    """Test non-English language detection"""
    text = "这是中文文本"
    assert detect_language(text) == "unknown"


def test_title_similarity_identical():
    """Test similarity of identical titles"""
    title1 = "Breaking news from Washington"
    title2 = "Breaking news from Washington"
    assert calculate_title_similarity(title1, title2) == 1.0


def test_title_similarity_high():
    """Test high similarity titles"""
    title1 = "Major earthquake strikes California coast"
    title2 = "Earthquake strikes California coast"
    similarity = calculate_title_similarity(title1, title2)
    assert similarity > 0.8


def test_title_similarity_low():
    """Test low similarity titles"""
    title1 = "Weather forecast for tomorrow"
    title2 = "Stock market reaches new high"
    similarity = calculate_title_similarity(title1, title2)
    assert similarity < 0.3


def test_normalize_url():
    """Test URL normalization"""
    url = "https://example.com/article?utm_source=twitter  "
    normalized = normalize_url(url)
    assert normalized == "https://example.com/article?utm_source=twitter"
