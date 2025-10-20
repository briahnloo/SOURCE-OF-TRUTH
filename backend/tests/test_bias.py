"""
Tests for bias analysis and source classification
"""

import json
import pytest
from dataclasses import asdict

# Try to import the bias module
try:
    from app.services.bias import BiasAnalyzer, BiasScore

    BIAS_AVAILABLE = True
except ImportError:
    BIAS_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Requires full app environment")


def test_bias_analyzer_loads_metadata():
    """Test that BiasAnalyzer can load metadata"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()
    assert analyzer.metadata is not None
    assert isinstance(analyzer.metadata, dict)


def test_get_source_bias():
    """Test getting bias scores for a known source"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()

    # Test with BBC (should be in metadata)
    bias = analyzer.get_source_bias("feeds.bbci.co.uk")

    if bias is not None:  # Only test if source is classified
        assert isinstance(bias, BiasScore)

        # Check that geographic scores sum to approximately 1.0
        geo_sum = sum(bias.geographic.values())
        assert 0.99 <= geo_sum <= 1.01, f"Geographic scores sum to {geo_sum}, expected ~1.0"

        # Check that political scores sum to approximately 1.0
        pol_sum = sum(bias.political.values())
        assert 0.99 <= pol_sum <= 1.01, f"Political scores sum to {pol_sum}, expected ~1.0"

        # Check that tone scores sum to approximately 1.0
        tone_sum = sum(bias.tone.values())
        assert 0.99 <= tone_sum <= 1.01, f"Tone scores sum to {tone_sum}, expected ~1.0"

        # Check that detail scores sum to approximately 1.0
        detail_sum = sum(bias.detail.values())
        assert 0.99 <= detail_sum <= 1.01, f"Detail scores sum to {detail_sum}, expected ~1.0"


def test_get_source_bias_unknown_source():
    """Test that unknown sources return None"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()
    bias = analyzer.get_source_bias("unknown-source-12345.com")
    assert bias is None


def test_calculate_event_bias():
    """Test calculating aggregate bias for an event"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()

    # Test with mix of sources (some classified, some not)
    sources = [
        "feeds.bbci.co.uk",
        "aljazeera.com",
        "rss.nytimes.com",
        "unknown-source.com",  # This should be ignored
    ]

    bias = analyzer.calculate_event_bias(sources)

    assert isinstance(bias, BiasScore)

    # Verify all dimensions exist
    assert "western" in bias.geographic
    assert "eastern" in bias.geographic
    assert "global_south" in bias.geographic

    assert "left" in bias.political
    assert "center" in bias.political
    assert "right" in bias.political

    assert "sensational" in bias.tone
    assert "factual" in bias.tone

    assert "surface" in bias.detail
    assert "deep" in bias.detail


def test_calculate_event_bias_all_unknown():
    """Test that all unknown sources return neutral defaults"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()

    # All unknown sources
    sources = ["unknown1.com", "unknown2.com", "unknown3.com"]

    bias = analyzer.calculate_event_bias(sources)

    assert isinstance(bias, BiasScore)

    # Should return neutral defaults
    # Geographic should be roughly equal
    assert 0.3 <= bias.geographic["western"] <= 0.4
    assert 0.3 <= bias.geographic["eastern"] <= 0.4
    assert 0.3 <= bias.geographic["global_south"] <= 0.4


def test_bias_score_serialization():
    """Test that BiasScore can be serialized to JSON"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    bias = BiasScore(
        geographic={"western": 0.7, "eastern": 0.2, "global_south": 0.1},
        political={"left": 0.3, "center": 0.6, "right": 0.1},
        tone={"sensational": 0.2, "factual": 0.8},
        detail={"surface": 0.3, "deep": 0.7},
    )

    # Should be serializable
    bias_dict = asdict(bias)
    json_str = json.dumps(bias_dict)

    # Should be deserializable
    parsed = json.loads(json_str)
    assert parsed["geographic"]["western"] == 0.7
    assert parsed["political"]["center"] == 0.6
    assert parsed["tone"]["factual"] == 0.8
    assert parsed["detail"]["deep"] == 0.7


def test_extract_domain():
    """Test domain extraction from various source formats"""
    if not BIAS_AVAILABLE:
        pytest.skip("Bias module not available")

    analyzer = BiasAnalyzer()

    # Test URL with http
    assert analyzer._extract_domain("http://bbc.co.uk/news") == "bbc.co.uk"

    # Test URL with https
    assert analyzer._extract_domain("https://www.nytimes.com/article") == "nytimes.com"

    # Test plain domain
    assert analyzer._extract_domain("aljazeera.com") == "aljazeera.com"

    # Test with www prefix
    assert analyzer._extract_domain("www.theguardian.com") == "theguardian.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

