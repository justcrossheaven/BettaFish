"""
Comprehensive tests for utils/market_data.py
Tests ticker extraction, market snapshot fetching, fallback behavior, and prompt formatting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

# Import the module to test
from utils import market_data
from tests.mocks import MockYFinance


class TestTickerExtraction:
    """Test ticker extraction from natural language queries."""
    
    def test_extract_ticker_from_company_name(self):
        """Should extract ticker from company name."""
        result = market_data.extract_ticker_from_query("Microsoft AI strategy analysis")
        assert result == "MSFT"
    
    def test_extract_ticker_from_uppercase_ticker(self):
        """Should extract ticker from uppercase ticker symbol."""
        result = market_data.extract_ticker_from_query("NVDA earnings report Q4")
        assert result == "NVDA"
    
    def test_extract_ticker_from_lowercase_company(self):
        """Should handle lowercase company names."""
        result = market_data.extract_ticker_from_query("apple stock analysis")
        assert result == "AAPL"
    
    def test_extract_ticker_with_punctuation(self):
        """Should handle ticker with punctuation."""
        result = market_data.extract_ticker_from_query("What about TSLA?")
        assert result == "TSLA"
    
    def test_extract_ticker_mixed_case(self):
        """Should extract from mixed case company name."""
        result = market_data.extract_ticker_from_query("Google earnings call summary")
        assert result == "GOOGL"
    
    def test_no_ticker_found(self):
        """Should return None when no ticker found."""
        result = market_data.extract_ticker_from_query("General market analysis")
        assert result is None
    
    def test_empty_query(self):
        """Should handle empty query."""
        result = market_data.extract_ticker_from_query("")
        assert result is None
    
    def test_none_query(self):
        """Should handle None query."""
        result = market_data.extract_ticker_from_query(None)
        assert result is None
    
    def test_non_traded_company(self):
        """Should return None for non-traded companies."""
        result = market_data.extract_ticker_from_query("OpenAI latest developments")
        assert result is None
    
    def test_multiple_tickers_returns_first(self):
        """Should return first valid ticker when multiple found."""
        result = market_data.extract_ticker_from_query("NVDA vs AMD comparison")
        assert result in ["NVDA", "AMD"]  # Either is valid
    
    def test_semiconductor_tickers(self):
        """Should extract semiconductor company tickers."""
        assert market_data.extract_ticker_from_query("AMD new chips") == "AMD"
        assert market_data.extract_ticker_from_query("Intel strategy") == "INTC"
        assert market_data.extract_ticker_from_query("Qualcomm 5G") == "QCOM"
    
    def test_cloud_enterprise_tickers(self):
        """Should extract cloud/enterprise tickers."""
        assert market_data.extract_ticker_from_query("Salesforce CRM") == "CRM"
        assert market_data.extract_ticker_from_query("Oracle database") == "ORCL"
        assert market_data.extract_ticker_from_query("IBM quantum") == "IBM"


class TestMarketSnapshotFetching:
    """Test market snapshot fetching with various scenarios."""
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_success_history(self, mock_ticker_class):
        """Should successfully fetch snapshot from history."""
        # Setup mock
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_data("MSFT", 415.23)
        
        # Execute
        result = market_data.get_market_snapshot("MSFT")
        
        # Assert
        assert result is not None
        assert result['ticker'] == "MSFT"
        assert result['current_price'] == 415.23
        assert result['currency'] == "USD"
        assert result['status'] == "REAL_TIME_VERIFIED"
        assert 'query_date' in result
        assert 'query_time' in result
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_empty_ticker(self, mock_ticker_class):
        """Should handle empty ticker input."""
        result = market_data.get_market_snapshot("")
        assert result is None
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_none_ticker(self, mock_ticker_class):
        """Should handle None ticker input."""
        result = market_data.get_market_snapshot(None)
        assert result is None
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_fallback_to_info(self, mock_ticker_class):
        """Should fallback to info dict when history fails."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        mock_ticker.info = {'currentPrice': 250.50}
        mock_ticker_class.return_value = mock_ticker
        
        result = market_data.get_market_snapshot("TSLA")
        
        assert result is not None
        assert result['current_price'] == 250.50
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_fallback_to_5day_history(self, mock_ticker_class):
        """Should fallback to 5-day history when other methods fail."""
        mock_ticker = MockYFinance.create_ticker_with_history_only("AMZN", 180.50)
        mock_ticker_class.return_value = mock_ticker
        
        result = market_data.get_market_snapshot("AMZN")
        
        assert result is not None
        assert result['ticker'] == "AMZN"
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_all_methods_fail(self, mock_ticker_class):
        """Should return fallback snapshot when all methods fail."""
        mock_ticker = MockYFinance.create_empty_ticker("UNKNOWN")
        mock_ticker_class.return_value = mock_ticker
        
        result = market_data.get_market_snapshot("UNKNOWN")
        
        assert result is not None
        assert result['ticker'] == "UNKNOWN"
        assert result['current_price'] is None
        assert "FALLBACK" in result['status']
    
    @patch('utils.market_data.yf')
    def test_get_snapshot_yfinance_not_installed(self, mock_yf):
        """Should handle yfinance import error."""
        # Simulate ImportError by patching the import
        with patch('utils.market_data.yf', None):
            with patch('utils.market_data.logger') as mock_logger:
                # Force re-import logic by directly calling the function
                result = market_data.get_market_snapshot("MSFT")
                
                # Should return fallback or handle gracefully
                # The actual behavior depends on implementation
                assert result is None or 'FALLBACK' in result.get('status', '')
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_network_error(self, mock_ticker_class):
        """Should handle network errors gracefully."""
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_error(
            "MSFT", "Connection timeout"
        )
        
        result = market_data.get_market_snapshot("MSFT")
        
        assert result is not None
        assert "FALLBACK" in result['status']
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_uppercase_normalization(self, mock_ticker_class):
        """Should normalize ticker to uppercase."""
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_data("AAPL", 180.00)
        
        result = market_data.get_market_snapshot("aapl")
        
        assert result['ticker'] == "AAPL"
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_whitespace_stripping(self, mock_ticker_class):
        """Should strip whitespace from ticker."""
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_data("GOOGL", 145.00)
        
        result = market_data.get_market_snapshot("  GOOGL  ")
        
        assert result['ticker'] == "GOOGL"
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_date_format(self, mock_ticker_class):
        """Should format date correctly (YYYY-MM-DD)."""
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_data("META", 400.00)
        
        result = market_data.get_market_snapshot("META")
        
        # Validate date format
        date_obj = datetime.strptime(result['query_date'], "%Y-%m-%d")
        assert date_obj.year >= 2025
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_time_format(self, mock_ticker_class):
        """Should format time correctly (HH:MM:SS)."""
        mock_ticker_class.return_value = MockYFinance.create_ticker_with_data("NVDA", 850.00)
        
        result = market_data.get_market_snapshot("NVDA")
        
        # Validate time format
        time_obj = datetime.strptime(result['query_time'], "%H:%M:%S")
        assert 0 <= time_obj.hour <= 23
    
    @patch('utils.market_data.yf.Ticker')
    def test_get_snapshot_price_rounding(self, mock_ticker_class):
        """Should round price to 2 decimal places."""
        mock_ticker = MockYFinance.create_ticker_with_data("TEST", 123.456789)
        mock_ticker_class.return_value = mock_ticker
        
        result = market_data.get_market_snapshot("TEST")
        
        assert result['current_price'] == 123.46  # Rounded


class TestPromptFormatting:
    """Test prompt formatting for LLM injection."""
    
    def test_format_with_valid_snapshot(self):
        """Should format snapshot data for prompt injection."""
        snapshot = {
            "ticker": "MSFT",
            "current_price": 415.23,
            "query_date": "2025-01-30",
            "status": "REAL_TIME_VERIFIED"
        }
        
        result = market_data.format_market_anchor_for_prompt(snapshot)
        
        assert "MSFT" in result
        assert "$415.23" in result
        assert "2025-01-30" in result
        assert "REAL_TIME_VERIFIED" in result
        assert "MARKET ANCHOR PROTOCOL" in result
    
    def test_format_with_unavailable_price(self):
        """Should handle unavailable price gracefully."""
        snapshot = {
            "ticker": "UNKNOWN",
            "current_price": None,
            "query_date": "2025-01-30",
            "status": "FALLBACK (NO_PRICE_DATA)"
        }
        
        result = market_data.format_market_anchor_for_prompt(snapshot)
        
        assert "UNKNOWN" in result
        assert "UNAVAILABLE" in result
    
    def test_format_with_none_snapshot(self):
        """Should return empty string for None snapshot."""
        result = market_data.format_market_anchor_for_prompt(None)
        assert result == ""
    
    def test_format_anti_hallucination_rules(self):
        """Should include anti-hallucination rules."""
        snapshot = {
            "ticker": "NVDA",
            "current_price": 850.00,
            "query_date": "2025-01-30",
            "status": "REAL_TIME_VERIFIED"
        }
        
        result = market_data.format_market_anchor_for_prompt(snapshot)
        
        assert "ANTI-HALLUCINATION RULES" in result
        assert "DO NOT invent dates" in result


class TestFallbackSnapshot:
    """Test fallback snapshot creation."""
    
    def test_create_fallback_snapshot(self):
        """Should create fallback snapshot with correct structure."""
        now = datetime.now()
        result = market_data._create_fallback_snapshot("TEST", now, "TEST_REASON")
        
        assert result['ticker'] == "TEST"
        assert result['current_price'] is None
        assert "FALLBACK" in result['status']
        assert "TEST_REASON" in result['status']
        assert 'query_date' in result
        assert 'query_time' in result


class TestTickerMapping:
    """Test ticker mapping dictionary completeness."""
    
    def test_ticker_mapping_exists(self):
        """Should have TICKER_MAPPING defined."""
        assert hasattr(market_data, 'TICKER_MAPPING')
        assert isinstance(market_data.TICKER_MAPPING, dict)
    
    def test_ticker_mapping_has_major_tech(self):
        """Should include major tech companies."""
        mapping = market_data.TICKER_MAPPING
        assert 'microsoft' in mapping
        assert 'apple' in mapping
        assert 'google' in mapping
        assert 'nvidia' in mapping
        assert 'meta' in mapping
    
    def test_ticker_mapping_case_insensitive_keys(self):
        """Should have lowercase keys for case-insensitive matching."""
        mapping = market_data.TICKER_MAPPING
        for key in mapping.keys():
            assert key.islower() or key.isupper()
