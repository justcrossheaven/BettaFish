"""
Mock yfinance module for testing market data functionality.
"""

import pandas as pd
from unittest.mock import Mock


class MockYFinance:
    """Mock implementation of yfinance for testing."""
    
    @staticmethod
    def create_ticker_with_data(symbol="MSFT", price=415.23):
        """Create a mock ticker with realistic data."""
        mock_ticker = Mock()
        
        # Mock history DataFrame
        history_df = pd.DataFrame({
            'Close': [price],
            'Open': [price * 0.99],
            'High': [price * 1.02],
            'Low': [price * 0.98],
            'Volume': [25000000]
        })
        mock_ticker.history.return_value = history_df
        
        # Mock info dict
        mock_ticker.info = {
            'currentPrice': price,
            'regularMarketPrice': price,
            'symbol': symbol,
            'longName': f'{symbol} Corporation'
        }
        
        return mock_ticker
    
    @staticmethod
    def create_empty_ticker(symbol="UNKNOWN"):
        """Create a mock ticker with no data."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker.info = {}
        return mock_ticker
    
    @staticmethod
    def create_ticker_with_history_only(symbol="TSLA", price=250.50):
        """Create a ticker where only history() works."""
        mock_ticker = Mock()
        
        history_df = pd.DataFrame({
            'Close': [price, price * 1.02, price * 0.98],
            'Open': [price * 0.99, price, price * 1.01],
            'High': [price * 1.03, price * 1.04, price * 1.02],
            'Low': [price * 0.97, price * 0.98, price * 0.96],
            'Volume': [30000000, 28000000, 32000000]
        })
        mock_ticker.history.return_value = history_df
        mock_ticker.info = {}  # Empty info
        
        return mock_ticker
    
    @staticmethod
    def create_ticker_with_error(symbol="ERROR", error_msg="API Error"):
        """Create a ticker that raises an error."""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception(error_msg)
        mock_ticker.info = {}
        return mock_ticker
