"""Tests for truth confidence scoring"""

import pytest
from app.services.score import (
    calculate_evidence_score,
    calculate_geo_score,
    calculate_source_score,
)


def test_source_score_single_source():
    """Test source score with 1 source"""
    score = calculate_source_score(1)
    assert score == 5.0  # 1/5 * 25


def test_source_score_optimal():
    """Test source score with 5 sources (optimal)"""
    score = calculate_source_score(5)
    assert score == 25.0  # 5/5 * 25


def test_source_score_capped():
    """Test source score is capped at 25"""
    score = calculate_source_score(10)
    assert score == 25.0  # Capped at max


def test_geo_score_low_diversity():
    """Test geo score with low diversity"""
    score = calculate_geo_score(0.25)  # 1 country out of 4
    assert score == 10.0  # 0.25 * 40


def test_geo_score_high_diversity():
    """Test geo score with high diversity"""
    score = calculate_geo_score(1.0)  # 4+ countries
    assert score == 40.0  # 1.0 * 40


def test_evidence_score_present():
    """Test evidence score when official source present"""
    score = calculate_evidence_score(True)
    assert score == 20.0


def test_evidence_score_absent():
    """Test evidence score when no official source"""
    score = calculate_evidence_score(False)
    assert score == 0.0


def test_combined_score_perfect():
    """Test perfect truth score (100)"""
    source_score = calculate_source_score(10)  # 25
    geo_score = calculate_geo_score(1.0)  # 40
    evidence_score = calculate_evidence_score(True)  # 20
    official_score = 15.0  # Maximum

    total = source_score + geo_score + evidence_score + official_score
    assert total == 100.0


def test_combined_score_minimal():
    """Test minimal truth score"""
    source_score = calculate_source_score(1)  # 5
    geo_score = calculate_geo_score(0.0)  # 0
    evidence_score = calculate_evidence_score(False)  # 0
    official_score = 0.0  # None

    total = source_score + geo_score + evidence_score + official_score
    assert total == 5.0
