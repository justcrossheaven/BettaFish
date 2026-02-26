"""
Test suite for Market Data Utility (Anti-Hallucination Module)

Tests the core functions:
- extract_ticker_from_query()
- get_market_snapshot()
- format_market_anchor_for_prompt()
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.market_data import (
    extract_ticker_from_query,
    get_market_snapshot,
    format_market_anchor_for_prompt,
    TICKER_MAPPING,
)


class TestTickerExtraction:
    """Tests for extract_ticker_from_query function."""
    
    def test_extract_company_name(self):
        """Should extract ticker from company name."""
        assert extract_ticker_from_query("Microsoft stock analysis") == "MSFT"
        assert extract_ticker_from_query("Apple earnings report") == "AAPL"
        assert extract_ticker_from_query("What is NVIDIA's PE ratio?") == "NVDA"
    
    def test_extract_ticker_symbol(self):
        """Should extract ticker from explicit ticker symbol."""
        assert extract_ticker_from_query("NVDA earnings report") == "NVDA"
        assert extract_ticker_from_query("Analysis of TSLA growth") == "TSLA"
        assert extract_ticker_from_query("Is MSFT overvalued?") == "MSFT"
    
    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert extract_ticker_from_query("microsoft strategy") == "MSFT"
        assert extract_ticker_from_query("MICROSOFT strategy") == "MSFT"
        assert extract_ticker_from_query("MicroSoft strategy") == "MSFT"
    
    def test_no_ticker_found(self):
        """Should return None when no ticker is found."""
        assert extract_ticker_from_query("General market analysis") is None
        assert extract_ticker_from_query("Random text here") is None
        assert extract_ticker_from_query("") is None
        assert extract_ticker_from_query(None) is None
    
    def test_ticker_mapping_coverage(self):
        """Verify key companies are in the mapping."""
        key_companies = ["microsoft", "apple", "google", "amazon", "nvidia", "tesla"]
        for company in key_companies:
            assert company in TICKER_MAPPING, f"{company} not in TICKER_MAPPING"
            assert TICKER_MAPPING[company] is not None


class TestMarketSnapshot:
    """Tests for get_market_snapshot function."""
    
    def test_returns_dict_or_none(self):
        """Should return dict with required keys or None."""
        result = get_market_snapshot("MSFT")
        if result is not None:
            assert isinstance(result, dict)
            assert "ticker" in result
            assert "current_price" in result
            assert "query_date" in result
            assert "status" in result
    
    def test_empty_ticker(self):
        """Should return None for empty ticker."""
        assert get_market_snapshot("") is None
        assert get_market_snapshot(None) is None
    
    def test_uppercase_handling(self):
        """Should handle lowercase ticker input."""
        result = get_market_snapshot("msft")
        if result is not None:
            assert result["ticker"] == "MSFT"
    
    def test_invalid_ticker_returns_fallback(self):
        """Should return fallback for invalid tickers."""
        result = get_market_snapshot("ZZZZZ12345")
        if result is not None:
            # Should have fallback status
            assert "FALLBACK" in result.get("status", "") or result.get("current_price") is None


class TestFormatMarketAnchor:
    """Tests for format_market_anchor_for_prompt function."""
    
    def test_none_input(self):
        """Should return empty string for None input."""
        assert format_market_anchor_for_prompt(None) == ""
    
    def test_valid_snapshot(self):
        """Should format valid snapshot correctly."""
        snapshot = {
            "ticker": "MSFT",
            "current_price": 415.23,
            "query_date": "2025-01-30",
            "status": "REAL_TIME_VERIFIED"
        }
        result = format_market_anchor_for_prompt(snapshot)
        
        assert "MARKET ANCHOR PROTOCOL" in result
        assert "2025-01-30" in result
        assert "MSFT" in result
        assert "$415.23" in result
        assert "ANTI-HALLUCINATION" in result
    
    def test_unavailable_price(self):
        """Should handle None price gracefully."""
        snapshot = {
            "ticker": "MSFT",
            "current_price": None,
            "query_date": "2025-01-30",
            "status": "FALLBACK"
        }
        result = format_market_anchor_for_prompt(snapshot)
        
        assert "UNAVAILABLE" in result


def run_tests():
    """Run all tests and report results."""
    import traceback
    
    print("=" * 60)
    print("Market Data Utility Tests")
    print("=" * 60)
    print()
    
    test_classes = [
        TestTickerExtraction(),
        TestMarketSnapshot(),
        TestFormatMarketAnchor(),
    ]
    
    passed = 0
    failed = 0
    
    for test_instance in test_classes:
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            method = getattr(test_instance, method_name)
            full_name = f"{test_instance.__class__.__name__}.{method_name}"
            print(f"Running: {full_name}...", end=" ")
            
            try:
                method()
                print("✓ PASSED")
                passed += 1
            except AssertionError as e:
                print(f"✗ FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ ERROR: {e}")
                traceback.print_exc()
                failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
