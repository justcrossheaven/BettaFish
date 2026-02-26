"""
Tests for MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/reddit/client.py
Tests Reddit client functionality with mocked PRAW.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Skip tests if praw not available
pytest.importorskip("praw", reason="praw not installed")

from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit import client
from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.field import (
    RedditSortType, RedditTimeFilter
)
from tests.mocks import MockPRAW


class TestRedditClientInitialization:
    """Test RedditClient initialization."""
    
    def test_init_with_credentials(self, mock_env_vars):
        """Should initialize with provided credentials."""
        rc = client.RedditClient(
            client_id="test_id",
            client_secret="test_secret"
        )
        assert rc.client_id == "test_id"
        assert rc.client_secret == "test_secret"
        assert rc._initialized == False
    
    def test_init_from_env_vars(self, mock_env_vars):
        """Should read credentials from environment variables."""
        rc = client.RedditClient()
        assert rc.client_id == "test_client_id"
        assert rc.client_secret == "test_client_secret"
        assert rc.user_agent == "BettaFish/Test"
    
    def test_init_without_credentials(self, clear_env_vars):
        """Should initialize without credentials (will fail on use)."""
        rc = client.RedditClient()
        assert rc.client_id is None
        assert rc.client_secret is None
    
    def test_default_subreddit_lists(self):
        """Should have default finance and tech subreddit lists."""
        rc = client.RedditClient()
        assert len(rc.FINANCE_SUBREDDITS) > 0
        assert 'wallstreetbets' in rc.FINANCE_SUBREDDITS
        assert len(rc.TECH_SUBREDDITS) > 0


class TestRedditClientInitializationProcess:
    """Test _ensure_initialized method."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_ensure_initialized_success(self, mock_praw_reddit, mock_env_vars):
        """Should successfully initialize PRAW client."""
        mock_praw_reddit.return_value = MockPRAW.create_reddit_client()
        
        rc = client.RedditClient()
        result = rc._ensure_initialized()
        
        assert result == True
        assert rc._initialized == True
        mock_praw_reddit.assert_called_once()
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_ensure_initialized_already_initialized(self, mock_praw_reddit):
        """Should return True if already initialized."""
        rc = client.RedditClient()
        rc._initialized = True
        
        result = rc._ensure_initialized()
        
        assert result == True
        mock_praw_reddit.assert_not_called()
    
    def test_ensure_initialized_no_credentials(self, clear_env_vars):
        """Should return False when no credentials provided."""
        rc = client.RedditClient()
        result = rc._ensure_initialized()
        
        assert result == False
        assert rc._initialized == False
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_ensure_initialized_praw_error(self, mock_praw_reddit, mock_env_vars):
        """Should handle PRAW initialization errors."""
        mock_praw_reddit.side_effect = Exception("PRAW Error")
        
        rc = client.RedditClient()
        result = rc._ensure_initialized()
        
        assert result == False
        assert rc._initialized == False


class TestSearchPosts:
    """Test search_posts method."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_search_posts_success(self, mock_praw_reddit, mock_env_vars):
        """Should successfully search posts."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.search_posts("NVDA earnings", limit=10)
        
        assert len(results) > 0
        assert isinstance(results[0], dict)
        assert 'post_id' in results[0]
        assert 'title' in results[0]
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_search_posts_custom_subreddits(self, mock_praw_reddit, mock_env_vars):
        """Should search specific subreddits."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.search_posts(
            "AMD",
            subreddits=["stocks", "AMD_Stock"],
            limit=5
        )
        
        assert isinstance(results, list)
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_search_posts_with_sort_and_time_filter(self, mock_praw_reddit, mock_env_vars):
        """Should apply sort and time filter parameters."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.search_posts(
            "Tesla",
            sort=RedditSortType.NEW,
            time_filter=RedditTimeFilter.DAY,
            limit=10
        )
        
        assert isinstance(results, list)
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_search_posts_with_callback(self, mock_praw_reddit, mock_env_vars):
        """Should call callback for each post."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        callback_results = []
        def callback(post):
            callback_results.append(post)
        
        rc = client.RedditClient()
        results = rc.search_posts("AAPL", limit=5, callback=callback)
        
        assert len(callback_results) > 0
        assert len(callback_results) == len(results)
    
    def test_search_posts_not_initialized(self, clear_env_vars):
        """Should return empty list if not initialized."""
        rc = client.RedditClient()
        results = rc.search_posts("query")
        
        assert results == []


class TestGetHotPosts:
    """Test get_hot_posts method."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_hot_posts_success(self, mock_praw_reddit, mock_env_vars):
        """Should get hot posts from subreddit."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.get_hot_posts("wallstreetbets", limit=10)
        
        assert len(results) > 0
        assert isinstance(results[0], dict)
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_hot_posts_with_callback(self, mock_praw_reddit, mock_env_vars):
        """Should call callback for each post."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        callback_count = 0
        def callback(post):
            nonlocal callback_count
            callback_count += 1
        
        rc = client.RedditClient()
        results = rc.get_hot_posts("stocks", limit=5, callback=callback)
        
        assert callback_count > 0


class TestGetNewPosts:
    """Test get_new_posts method."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_new_posts_success(self, mock_praw_reddit, mock_env_vars):
        """Should get new posts from subreddit."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.get_new_posts("investing", limit=10)
        
        assert len(results) > 0
        assert isinstance(results[0], dict)


class TestGetPostComments:
    """Test get_post_comments method."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_post_comments_success(self, mock_praw_reddit, mock_env_vars):
        """Should get comments from a post."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.get_post_comments("abc123", limit=50)
        
        assert len(results) > 0
        assert isinstance(results[0], dict)
        assert 'comment_id' in results[0]
        assert 'body' in results[0]
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_post_comments_with_callback(self, mock_praw_reddit, mock_env_vars):
        """Should call callback for each comment."""
        mock_reddit = MockPRAW.create_reddit_client()
        mock_praw_reddit.return_value = mock_reddit
        
        callback_results = []
        def callback(comment):
            callback_results.append(comment)
        
        rc = client.RedditClient()
        results = rc.get_post_comments("abc123", limit=10, callback=callback)
        
        assert len(callback_results) > 0


class TestParseSubmission:
    """Test _parse_submission method."""
    
    def test_parse_submission_complete_data(self):
        """Should parse submission with all data."""
        submission = MockPRAW.create_submission()
        
        rc = client.RedditClient()
        result = rc._parse_submission(submission)
        
        assert result['post_id'] == "abc123"
        assert result['title'] == "Test Post"
        assert result['subreddit'] == "wallstreetbets"
        assert result['author'] == "test_user"
        assert result['score'] == 100
        assert 'created_at' in result
        assert 'permalink' in result
    
    def test_parse_submission_deleted_author(self):
        """Should handle deleted author."""
        submission = MockPRAW.create_submission()
        submission.author = None
        
        rc = client.RedditClient()
        result = rc._parse_submission(submission)
        
        assert result['author'] == "[deleted]"
    
    def test_parse_submission_long_text_truncated(self):
        """Should truncate long selftext."""
        submission = MockPRAW.create_submission()
        submission.selftext = "x" * 5000
        
        rc = client.RedditClient()
        result = rc._parse_submission(submission)
        
        assert len(result['text']) <= 2000


class TestParseComment:
    """Test _parse_comment method."""
    
    def test_parse_comment_complete_data(self):
        """Should parse comment with all data."""
        comment = MockPRAW.create_comment()
        
        rc = client.RedditClient()
        result = rc._parse_comment(comment)
        
        assert result['comment_id'] == "xyz789"
        assert result['body'] == "Great post!"
        assert result['author'] == "commenter"
        assert result['score'] == 25
        assert 'created_at' in result
    
    def test_parse_comment_deleted_author(self):
        """Should handle deleted comment author."""
        comment = MockPRAW.create_comment()
        comment.author = None
        
        rc = client.RedditClient()
        result = rc._parse_comment(comment)
        
        assert result['author'] == "[deleted]"
    
    def test_parse_comment_long_body_truncated(self):
        """Should truncate long comment body."""
        comment = MockPRAW.create_comment()
        comment.body = "x" * 2000
        
        rc = client.RedditClient()
        result = rc._parse_comment(comment)
        
        assert len(result['body']) <= 1000


class TestErrorHandling:
    """Test error handling."""
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_search_posts_exception_handled(self, mock_praw_reddit, mock_env_vars):
        """Should handle exceptions during search."""
        mock_reddit = Mock()
        mock_reddit.subreddit.side_effect = Exception("API Error")
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.search_posts("query")
        
        # Should return empty list on error, not crash
        assert results == []
    
    @patch('MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit.client.praw.Reddit')
    def test_get_post_comments_exception_handled(self, mock_praw_reddit, mock_env_vars):
        """Should handle exceptions when getting comments."""
        mock_reddit = Mock()
        mock_reddit.submission.side_effect = Exception("Not Found")
        mock_praw_reddit.return_value = mock_reddit
        
        rc = client.RedditClient()
        results = rc.get_post_comments("invalid_id")
        
        assert results == []
