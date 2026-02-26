"""
Tests for QueryEngine tools (reddit_search.py and twitter_search.py)
Tests search functionality with mocked clients.
"""

import pytest
import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Skip if dependencies not available
pytest.importorskip("praw", reason="praw not installed")

from tests.mocks import MockPRAW, MockTwikit


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


PROJECT_ROOT = Path(__file__).resolve().parent.parent
reddit_search = _load_module("qe_reddit_search", PROJECT_ROOT / "QueryEngine/tools/reddit_search.py")
twitter_search = _load_module("qe_twitter_search", PROJECT_ROOT / "QueryEngine/tools/twitter_search.py")


class TestRedditSearchClient:
    """Test RedditSearchClient class."""
    
    @patch.object(reddit_search.praw, 'Reddit')
    def test_init_with_credentials(self, mock_praw, mock_env_vars):
        """Should initialize with credentials."""
        client = reddit_search.RedditSearchClient(
            client_id="test_id",
            client_secret="test_secret"
        )
        assert client.client_id == "test_id"
    
    @patch.object(reddit_search.praw, 'Reddit')
    def test_search_posts_success(self, mock_praw, mock_env_vars):
        """Should search posts successfully."""
        mock_praw.return_value = MockPRAW.create_reddit_client()
        
        client = reddit_search.RedditSearchClient()
        response = client.search_posts("NVDA", limit=5)
        
        assert response is not None
        assert len(response.posts) > 0
        assert response.query == "NVDA"
    
    @patch.object(reddit_search.praw, 'Reddit')
    def test_search_by_ticker(self, mock_praw, mock_env_vars):
        """Should search by ticker."""
        mock_praw.return_value = MockPRAW.create_reddit_client()
        
        client = reddit_search.RedditSearchClient()
        response = client.search_by_ticker("AMD")
        
        assert response is not None
        assert "AMD" in response.query.upper()
    
    @patch.object(reddit_search.praw, 'Reddit')
    def test_get_hot_posts(self, mock_praw, mock_env_vars):
        """Should get hot posts."""
        mock_praw.return_value = MockPRAW.create_reddit_client()
        
        client = reddit_search.RedditSearchClient()
        response = client.get_hot_posts("wallstreetbets", limit=5)
        
        assert response is not None
        assert len(response.posts) > 0
    
    @patch.object(reddit_search.praw, 'Reddit')
    def test_get_post_comments(self, mock_praw, mock_env_vars):
        """Should get post comments."""
        mock_praw.return_value = MockPRAW.create_reddit_client()
        
        client = reddit_search.RedditSearchClient()
        response = client.get_post_comments("abc123", limit=10)
        
        assert response is not None
        assert len(response.comments) > 0
    
    def test_extract_tickers(self):
        """Should extract tickers from text."""
        text = "I'm bullish on $NVDA and $AMD but bearish on INTC"
        tickers = reddit_search.extract_tickers(text)
        
        assert "NVDA" in tickers
        assert "AMD" in tickers
        assert "INTC" in tickers
    
    def test_extract_tickers_filters_common_words(self):
        """Should filter out common words."""
        text = "THE company HAS great VALUE and FOR investors"
        tickers = reddit_search.extract_tickers(text)
        
        # Common words should be filtered
        assert "THE" not in tickers
        assert "HAS" not in tickers
        assert "FOR" not in tickers


class TestTwitterSearchClient:
    """Test TwitterSearchClient class."""
    
    @pytest.mark.asyncio
    @patch.object(twitter_search, 'TwikitClient')
    async def test_init_with_credentials(self, mock_client_class, mock_env_vars):
        """Should initialize with credentials."""
        client = twitter_search.TwitterSearchClient(
            username="test",
            email="test@test.com",
            password="pass"
        )
        assert client.username == "test"
    
    @pytest.mark.asyncio
    @patch.object(twitter_search, 'TwikitClient')
    async def test_search_tweets_success(self, mock_client_class, mock_env_vars):
        """Should search tweets successfully."""
        mock_client_class.return_value = MockTwikit.create_client()
        
        client = twitter_search.TwitterSearchClient()
        response = await client.search_tweets("$NVDA", max_results=5)
        
        assert response is not None
        assert len(response.results) > 0
        assert response.query == "$NVDA"
    
    @pytest.mark.asyncio
    @patch.object(twitter_search, 'TwikitClient')
    async def test_search_by_ticker(self, mock_client_class, mock_env_vars):
        """Should search by ticker."""
        mock_client_class.return_value = MockTwikit.create_client()
        
        client = twitter_search.TwitterSearchClient()
        response = await client.search_tweets_by_ticker("AMD", max_results=5)
        
        assert response is not None
        assert "$AMD" in response.query
    
    @pytest.mark.asyncio
    @patch.object(twitter_search, 'TwikitClient')
    async def test_get_user_tweets(self, mock_client_class, mock_env_vars):
        """Should get user tweets."""
        mock_client_class.return_value = MockTwikit.create_client()
        
        client = twitter_search.TwitterSearchClient()
        response = await client.get_user_tweets("elonmusk", max_results=5)
        
        assert response is not None
        assert "from:elonmusk" in response.query
    
    def test_extract_tickers_from_tweet(self):
        """Should extract tickers from tweet text."""
        text = "$NVDA crushing it! Also watching $AMD"
        tickers = twitter_search.extract_tickers(text)
        
        assert "NVDA" in tickers
        assert "AMD" in tickers
    
    def test_search_tweets_sync(self, mock_env_vars):
        """Should provide synchronous wrapper."""
        with patch.object(twitter_search, 'TwikitClient') as mock_client_class:
            mock_client_class.return_value = MockTwikit.create_client()
            
            client = twitter_search.TwitterSearchClient()
            response = client.search_tweets_sync("test", max_results=5)
            
            assert response is not None


class TestRedditPostDataclass:
    """Test RedditPost dataclass."""
    
    def test_reddit_post_creation(self):
        """Should create RedditPost with required fields."""
        post = reddit_search.RedditPost(
            id="test123",
            title="Test Post",
            text="Test content",
            subreddit="stocks"
        )
        assert post.id == "test123"
        assert post.title == "Test Post"
        assert post.score == 0  # Default value


class TestRedditCommentDataclass:
    """Test RedditComment dataclass."""
    
    def test_reddit_comment_creation(self):
        """Should create RedditComment with required fields."""
        comment = reddit_search.RedditComment(
            id="comment123",
            body="Great analysis!"
        )
        assert comment.id == "comment123"
        assert comment.body == "Great analysis!"


class TestTwitterResponseDataclass:
    """Test TwitterResponse dataclass."""
    
    def test_twitter_response_creation(self):
        """Should create TwitterResponse."""
        response = twitter_search.TwitterResponse(query="test")
        assert response.query == "test"
        assert len(response.results) == 0
    
    def test_twitter_response_tweets_alias(self):
        """Should provide tweets alias for results."""
        tweet = twitter_search.TweetResult(id="123", text="Test")
        response = twitter_search.TwitterResponse(
            query="test",
            results=[tweet]
        )
        assert len(response.tweets) == 1
        assert response.tweets[0].id == "123"


class TestTweetResultDataclass:
    """Test TweetResult dataclass."""
    
    def test_tweet_result_creation(self):
        """Should create TweetResult with required fields."""
        tweet = twitter_search.TweetResult(
            id="123456",
            text="Test tweet about $NVDA"
        )
        assert tweet.id == "123456"
        assert tweet.text == "Test tweet about $NVDA"
    
    def test_tweet_result_author_username_alias(self):
        """Should provide author_username alias."""
        tweet = twitter_search.TweetResult(
            id="123",
            text="Test",
            user_screen_name="testuser"
        )
        assert tweet.author_username == "testuser"
    
    def test_tweet_result_like_count_alias(self):
        """Should provide like_count alias."""
        tweet = twitter_search.TweetResult(
            id="123",
            text="Test",
            favorite_count=100
        )
        assert tweet.like_count == 100


class TestUtilityFunctions:
    """Test utility and helper functions."""
    
    def test_print_reddit_response(self, capsys):
        """Should print Reddit response summary."""
        response = reddit_search.RedditResponse(query="test", response_time=0.0)
        reddit_search.print_reddit_response(response)
        captured = capsys.readouterr()
        assert "test" in captured.out
    
    def test_print_twitter_response(self, capsys):
        """Should print Twitter response summary."""
        response = twitter_search.TwitterResponse(query="test", response_time=0.0)
        twitter_search.print_twitter_response(response)
        captured = capsys.readouterr()
        assert "test" in captured.out
    
    def test_parse_submission_function(self):
        """Should parse PRAW submission to RedditPost."""
        submission = MockPRAW.create_submission()
        post = reddit_search.parse_submission(submission)
        
        assert isinstance(post, reddit_search.RedditPost)
        assert post.id == "abc123"
    
    def test_parse_comment_function(self):
        """Should parse PRAW comment to RedditComment."""
        comment = MockPRAW.create_comment()
        parsed = reddit_search.parse_comment(comment)
        
        assert isinstance(parsed, reddit_search.RedditComment)
        assert parsed.id == "xyz789"
    
    def test_parse_tweet_function(self):
        """Should parse twikit tweet to TweetResult."""
        tweet = MockTwikit.create_tweet()
        parsed = twitter_search.parse_tweet(tweet)
        
        assert isinstance(parsed, twitter_search.TweetResult)
        assert parsed.id == "1234567890"


class TestErrorHandling:
    """Test error handling in search tools."""
    
    def test_reddit_search_without_credentials(self, clear_env_vars):
        """Should handle missing credentials gracefully."""
        client = reddit_search.RedditSearchClient()
        response = client.search_posts("query")

        # In no-credential mode, implementation may gracefully fall back to public JSON.
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_twitter_search_without_credentials(self, clear_env_vars):
        """Should handle missing Twitter credentials."""
        client = twitter_search.TwitterSearchClient()
        response = await client.search_tweets("query")
        
        assert response.error is not None


class TestDefaultSubreddits:
    """Test default subreddit configurations."""
    
    def test_finance_subreddits_defined(self):
        """Should have finance subreddits defined."""
        assert len(reddit_search.RedditSearchClient.FINANCE_SUBREDDITS) > 0
        assert "wallstreetbets" in reddit_search.RedditSearchClient.FINANCE_SUBREDDITS
    
    def test_tech_subreddits_defined(self):
        """Should have tech subreddits defined."""
        assert len(reddit_search.RedditSearchClient.TECH_SUBREDDITS) > 0
    
    def test_all_default_subreddits(self):
        """Should combine finance and tech subreddits."""
        all_subs = reddit_search.RedditSearchClient.ALL_DEFAULT_SUBREDDITS
        assert len(all_subs) > len(reddit_search.RedditSearchClient.FINANCE_SUBREDDITS)
