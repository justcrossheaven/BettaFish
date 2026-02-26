import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd

from utils import market_data
from tests.mocks import MockYFinance


class TestTickerExtraction:
    def test_extract_ticker(self):
        assert market_data.extract_ticker_from_query("Microsoft AI strategy") == "MSFT"
        assert market_data.extract_ticker_from_query("NVDA earnings") == "NVDA"
        assert market_data.extract_ticker_from_query("OpenAI roadmap") is None
        assert market_data.extract_ticker_from_query("") is None


class TestMarketSnapshotFetching:
    def _patch_yfinance(self, ticker_obj):
        yf_mod = Mock()
        yf_mod.Ticker.return_value = ticker_obj
        return patch.dict("sys.modules", {"yfinance": yf_mod})

    def test_get_snapshot_success_history(self):
        with self._patch_yfinance(MockYFinance.create_ticker_with_data("MSFT", 415.23)):
            result = market_data.get_market_snapshot("MSFT")
        assert result["ticker"] == "MSFT"
        assert result["current_price"] == 415.23
        assert result["status"] == "REAL_TIME_VERIFIED"

    def test_get_snapshot_empty_or_none_ticker(self):
        assert market_data.get_market_snapshot("") is None
        assert market_data.get_market_snapshot(None) is None

    def test_get_snapshot_fallback_to_info(self):
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker.info = {"currentPrice": 250.50}
        with self._patch_yfinance(mock_ticker):
            result = market_data.get_market_snapshot("TSLA")
        assert result["current_price"] == 250.50

    def test_get_snapshot_all_methods_fail(self):
        with self._patch_yfinance(MockYFinance.create_empty_ticker("UNKNOWN")):
            result = market_data.get_market_snapshot("UNKNOWN")
        assert "FALLBACK" in result["status"]

    def test_get_snapshot_import_error(self):
        with patch.dict("sys.modules", {"yfinance": None}):
            result = market_data.get_market_snapshot("MSFT")
        assert result is not None
        assert "FALLBACK" in result["status"]

    def test_normalization_and_formatting(self):
        with self._patch_yfinance(MockYFinance.create_ticker_with_data("AAPL", 123.456)):
            result = market_data.get_market_snapshot("  aapl ")
        assert result["ticker"] == "AAPL"
        assert result["current_price"] == 123.46
        datetime.strptime(result["query_date"], "%Y-%m-%d")
        datetime.strptime(result["query_time"], "%H:%M:%S")


class TestPromptFormatting:
    def test_format_market_anchor(self):
        snapshot = {
            "ticker": "MSFT",
            "current_price": 415.23,
            "query_date": "2025-01-30",
            "status": "REAL_TIME_VERIFIED",
        }
        out = market_data.format_market_anchor_for_prompt(snapshot)
        assert "MARKET ANCHOR PROTOCOL" in out
        assert "MSFT" in out

    def test_none_snapshot(self):
        assert market_data.format_market_anchor_for_prompt(None) == ""


class TestFallbackAndMapping:
    def test_fallback_snapshot(self):
        now = datetime.now()
        result = market_data._create_fallback_snapshot("TEST", now, "REASON")
        assert result["ticker"] == "TEST"
        assert "FALLBACK" in result["status"]

    def test_mapping_has_core_names(self):
        mapping = market_data.TICKER_MAPPING
        assert mapping["microsoft"] == "MSFT"
        assert mapping["apple"] == "AAPL"
