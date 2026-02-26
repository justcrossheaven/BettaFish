"""
Pytest Configuration and Shared Fixtures
Provides reusable fixtures for all test modules.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_yfinance_ticker():
    """Mock yfinance Ticker object with realistic data."""
    mock_ticker = Mock()
    
    # Mock history data
    import pandas as pd
    import numpy as np
    
    history_df = pd.DataFrame({
        'Close': [415.23],
        'Open': [410.50],
        'High': [418.00],
        'Low': [408.75],
        'Volume': [25000000]
    })
    mock_ticker.history.return_value = history_df
    
    # Mock info dict
    mock_ticker.info = {
        'currentPrice': 415.23,
        'regularMarketPrice': 415.23,
        'symbol': 'MSFT'
    }
    
    return mock_ticker


@pytest.fixture
def mock_yfinance_empty_ticker():
    """Mock yfinance Ticker with no data (for error cases)."""
    import pandas as pd
    
    mock_ticker = Mock()
    mock_ticker.history.return_value = pd.DataFrame()  # Empty DataFrame
    mock_ticker.info = {}
    return mock_ticker


@pytest.fixture
def sample_market_snapshot():
    """Sample market snapshot data."""
    return {
        "ticker": "MSFT",
        "current_price": 415.23,
        "currency": "USD",
        "query_date": "2025-01-30",
        "query_time": "14:30:00",
        "status": "REAL_TIME_VERIFIED"
    }


@pytest.fixture
def sample_reddit_post():
    """Sample Reddit post data."""
    return {
        "post_id": "abc123",
        "title": "NVDA earnings beat expectations!",
        "text": "NVIDIA just reported amazing Q4 results. Revenue up 265%!",
        "subreddit": "wallstreetbets",
        "author": "test_user",
        "score": 5420,
        "upvote_ratio": 0.92,
        "num_comments": 342,
        "created_utc": 1706637600,
        "created_at": "2025-01-30T14:00:00",
        "url": "https://reddit.com/test",
        "permalink": "https://reddit.com/r/wallstreetbets/comments/abc123",
        "is_self": True,
        "flair": "DD",
        "awards": 25
    }


@pytest.fixture
def sample_reddit_comment():
    """Sample Reddit comment data."""
    return {
        "comment_id": "xyz789",
        "body": "This is the way! $NVDA to the moon! 🚀",
        "author": "comment_user",
        "score": 150,
        "created_utc": 1706638800,
        "created_at": "2025-01-30T14:20:00",
        "parent_id": "t3_abc123",
        "is_submitter": False
    }


@pytest.fixture
def sample_tweet():
    """Sample Twitter tweet data."""
    return {
        "tweet_id": "1234567890",
        "text": "$NVDA just destroyed earnings! Data center revenue through the roof.",
        "created_at": "2025-01-30T15:00:00",
        "user_name": "Tech Investor",
        "user_screen_name": "techinvestor",
        "user_followers": 50000,
        "retweet_count": 250,
        "favorite_count": 1200,
        "reply_count": 85,
        "quote_count": 45,
        "view_count": 100000,
        "is_retweet": False,
        "hashtags": ["NVDA", "AI", "earnings"],
        "url": "https://twitter.com/i/status/1234567890"
    }


@pytest.fixture
def mock_praw_submission():
    """Mock PRAW submission object."""
    submission = Mock()
    submission.id = "abc123"
    submission.title = "NVDA earnings beat!"
    submission.selftext = "Full analysis here..."
    submission.subreddit = Mock()
    submission.subreddit.__str__ = lambda x: "wallstreetbets"
    submission.author = Mock()
    submission.author.__str__ = lambda x: "test_user"
    submission.score = 5420
    submission.upvote_ratio = 0.92
    submission.num_comments = 342
    submission.created_utc = 1706637600
    submission.url = "https://reddit.com/test"
    submission.permalink = "/r/wallstreetbets/comments/abc123"
    submission.is_self = True
    submission.link_flair_text = "DD"
    submission.total_awards_received = 25
    return submission


@pytest.fixture
def mock_praw_comment():
    """Mock PRAW comment object."""
    comment = Mock()
    comment.id = "xyz789"
    comment.body = "This is the way!"
    comment.author = Mock()
    comment.author.__str__ = lambda x: "comment_user"
    comment.score = 150
    comment.created_utc = 1706638800
    comment.parent_id = "t3_abc123"
    comment.is_submitter = False
    return comment


@pytest.fixture
def mock_twikit_tweet():
    """Mock twikit tweet object."""
    tweet = Mock()
    tweet.id = "1234567890"
    tweet.text = "$NVDA earnings amazing!"
    tweet.created_at = "2025-01-30T15:00:00"
    
    user = Mock()
    user.id = "987654321"
    user.name = "Tech Investor"
    user.screen_name = "techinvestor"
    user.followers_count = 50000
    
    tweet.user = user
    tweet.retweet_count = 250
    tweet.favorite_count = 1200
    tweet.reply_count = 85
    tweet.quote_count = 45
    tweet.view_count = 100000
    tweet.is_retweet = False
    tweet.hashtags = [{"text": "NVDA"}, {"text": "AI"}]
    
    return tweet


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for LLM testing."""
    client = Mock()
    client.generate_content.return_value = Mock(
        text="This is a generated response from Gemini."
    )
    return client


@pytest.fixture
def mock_gemini_cached_content():
    """Mock Gemini CachedContent object."""
    import datetime
    
    cached = Mock()
    cached.name = "bettafish_test_cache"
    cached.display_name = "bettafish_abc123"
    cached.expire_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return cached


# ============================================================================
# Environment Variable Fixtures
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "REDDIT_CLIENT_ID": "test_client_id",
        "REDDIT_CLIENT_SECRET": "test_client_secret",
        "REDDIT_USER_AGENT": "BettaFish/Test",
        "TWITTER_USERNAME": "test_user",
        "TWITTER_EMAIL": "test@example.com",
        "TWITTER_PASSWORD": "test_password",
        "TWITTER_COOKIES_PATH": "test_cookies.json",
        "GEMINI_API_KEY": "test_gemini_key"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def clear_env_vars(monkeypatch):
    """Clear all relevant environment variables."""
    env_vars = [
        "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT",
        "TWITTER_USERNAME", "TWITTER_EMAIL", "TWITTER_PASSWORD",
        "TWITTER_COOKIES_PATH", "GEMINI_API_KEY"
    ]
    
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for testing."""
    test_dir = tmp_path / "bettafish_test"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def temp_cookies_file(tmp_path):
    """Create a temporary cookies file."""
    cookies_file = tmp_path / "test_cookies.json"
    cookies_file.write_text('{"test": "cookie"}')
    return cookies_file


# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (requires full system)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (>1 second)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark E2E tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        # Mark unit tests by default
        else:
            if not any(marker in item.keywords for marker in ["integration", "e2e"]):
                item.add_marker(pytest.mark.unit)
