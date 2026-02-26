"""
Tests for MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/twitter/client.py
Tests Twitter client with mocked twikit.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Skip tests if twikit not available
pytest.importorskip("twikit", reason="twikit not installed")

from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter import client
from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.field import (
    TwitterSearchType, TwitterSortType
)
from tests.mocks import MockTwikit


class TestTwitterClientInitialization:
    """Test TwitterClient initialization."""
    
    def test_init_with_credentials(self, mock_env_vars):
        """Should initialize with credentials."""
        tc = client.TwitterClient(
            username="test",
            email="test@example.com",
            password="testpass"
        )
        assert tc.username == "test"
        assert tc.email == "test@example.com"
        assert tc._logged_in == False
    
    def test_init_from_env(self, mock_env_vars):
        """Should read from environment."""
        tc = client.TwitterClient()
        assert tc.username == "test_user"
        assert tc.email == "test@example.com"


class TestTwitterClientLogin:
    """Test login functionality."""
    
    @pytest.mark.asyncio
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.client.TwikitClient')
    async def test_login_with_cookies(self, mock_client_class, tmp_path):
        """Should load cookies if they exist."""
        # Create mock cookies file
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text('{"test": "cookie"}')
        
        mock_client = MockTwikit.create_client()
        mock_client_class.return_value = mock_client
        
        tc = client.TwitterClient(cookies_path=str(cookies_file))
        result = await tc.login()
        
        assert result == True
        assert tc._logged_in == True
    
    @pytest.mark.asyncio
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.client.TwikitClient')
    async def test_login_with_credentials(self, mock_client_class, mock_env_vars, tmp_path):
        """Should login with credentials if no cookies."""
        mock_client = MockTwikit.create_client()
        mock_client_class.return_value = mock_client
        
        cookies_path = tmp_path / "new_cookies.json"
        tc = client.TwitterClient(cookies_path=str(cookies_path))
        result = await tc.login()
        
        assert result == True
        mock_client.login.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_without_credentials(self, clear_env_vars):
        """Should fail without credentials."""
        tc = client.TwitterClient()
        result = await tc.login()
        
        assert result == False


class TestSearchTweets:
    """Test search_tweets method."""
    
    @pytest.mark.asyncio
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.client.TwikitClient')
    async def test_search_tweets_success(self, mock_client_class, mock_env_vars):
        """Should successfully search tweets."""
        mock_client = MockTwikit.create_client()
        mock_client_class.return_value = mock_client
        
        tc = client.TwitterClient()
        results = await tc.search_tweets("$NVDA", limit=10)
        
        assert len(results) > 0
        assert isinstance(results[0], dict)
        assert 'tweet_id' in results[0]
        assert 'text' in results[0]
    
    @pytest.mark.asyncio
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.client.TwikitClient')
    async def test_search_tweets_with_callback(self, mock_client_class, mock_env_vars):
        """Should call callback for each tweet."""
        mock_client = MockTwikit.create_client()
        mock_client_class.return_value = mock_client
        
        callback_count = 0
        async def callback(tweet):
            nonlocal callback_count
            callback_count += 1
        
        tc = client.TwitterClient()
        await tc.search_tweets("test", limit=5, callback=callback)
        
        assert callback_count > 0


class TestGetUserTweets:
    """Test get_user_tweets method."""
    
    @pytest.mark.asyncio
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter.client.TwikitClient')
    async def test_get_user_tweets_success(self, mock_client_class, mock_env_vars):
        """Should get user tweets."""
        mock_client = MockTwikit.create_client()
        mock_client_class.return_value = mock_client
        
        tc = client.TwitterClient()
        results = await tc.get_user_tweets("elonmusk", limit=10)
        
        assert isinstance(results, list)


class TestParseTweet:
    """Test _parse_tweet method."""
    
    def test_parse_tweet_complete_data(self):
        """Should parse tweet with all data."""
        tweet = MockTwikit.create_tweet()
        
        tc = client.TwitterClient()
        result = tc._parse_tweet(tweet)
        
        assert result['tweet_id'] == "1234567890"
        assert result['text'] == "Test tweet"
        assert result['user_name'] == "Test User"
        assert result['retweet_count'] == 50
    
    def test_parse_tweet_missing_user(self):
        """Should handle missing user."""
        tweet = Mock()
        tweet.id = "123"
        tweet.text = "Test"
        tweet.user = None
        tweet.retweet_count = 0
        tweet.favorite_count = 0
        tweet.reply_count = 0
        tweet.quote_count = 0
        tweet.view_count = None
        tweet.is_retweet = False
        tweet.hashtags = []
        
        tc = client.TwitterClient()
        result = tc._parse_tweet(tweet)
        
        assert result['user_name'] is None
