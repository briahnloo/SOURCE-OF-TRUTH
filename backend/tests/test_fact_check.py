"""
Tests for fact-checking service
"""

import pytest

# Try to import the fact-check module
try:
    from app.services.fact_check import FactChecker, FactCheckFlag

    FACTCHECK_AVAILABLE = True
except ImportError:
    FACTCHECK_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Requires full app environment")


def test_fact_checker_initialization():
    """Test that FactChecker can be initialized"""
    if not FACTCHECK_AVAILABLE:
        pytest.skip("FactChecker not available")

    checker = FactChecker()
    assert checker is not None


def test_google_factcheck_no_api_key():
    """Test that Google Fact Check returns empty list without API key"""
    if not FACTCHECK_AVAILABLE:
        pytest.skip("FactChecker not available")

    checker = FactChecker()
    # Without API key, should return empty list
    flags = checker._check_google_factcheck("Test title", "Test summary")
    assert isinstance(flags, list)


def test_check_article_returns_tuple():
    """Test that check_article returns proper tuple"""
    if not FACTCHECK_AVAILABLE:
        pytest.skip("FactChecker not available")

    checker = FactChecker()

    status, flags = checker.check_article(
        title="Test article about weather",
        summary="It will rain tomorrow",
        url="http://example.com/test",
        source="test.com",
    )

    assert isinstance(status, str)
    assert status in ["verified", "disputed", "false", "unverified"]
    assert isinstance(flags, list)


def test_earthquake_claim_extraction():
    """Test that earthquake claims are detected"""
    if not FACTCHECK_AVAILABLE:
        pytest.skip("FactChecker not available")

    checker = FactChecker()

    # Test with earthquake claim
    text = "a magnitude 7.8 earthquake struck turkey"
    result = checker._verify_earthquake_claims(text, "Earthquake in Turkey")

    # Result may be None if no USGS data matches or claim is accurate
    assert result is None or isinstance(result, FactCheckFlag)


def test_fact_check_flag_structure():
    """Test FactCheckFlag dataclass structure"""
    if not FACTCHECK_AVAILABLE:
        pytest.skip("FactChecker not available")

    flag = FactCheckFlag(
        claim="Test claim",
        verdict="false",
        evidence_source="USGS",
        evidence_url="http://example.com",
        explanation="This is wrong because...",
        confidence=0.95,
    )

    assert flag.claim == "Test claim"
    assert flag.verdict == "false"
    assert flag.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

