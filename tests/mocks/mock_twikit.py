"""
Mock twikit (Twitter) module for testing Twitter client functionality.
"""

from unittest.mock import Mock, AsyncMock


class MockTwikit:
    """Mock implementation of twikit for testing."""
    
    @staticmethod
    def create_tweet(tweet_id="1234567890", text="Test tweet", likes=100):
        """Create a mock tweet object."""
        tweet = Mock()
        tweet.id = tweet_id
        tweet.text = text
        tweet.created_at = "2025-01-30T15:00:00"
        tweet.retweet_count = 50
        tweet.favorite_count = likes
        tweet.reply_count = 25
        tweet.quote_count = 10
        tweet.view_count = 5000
        tweet.is_retweet = False
        tweet.hashtags = [{"text": "test"}]
        
        # Mock user
        user = Mock()
        user.id = "987654321"
        user.name = "Test User"
        user.screen_name = "testuser"
        user.followers_count = 10000
        
        tweet.user = user
        
        return tweet
    
    @staticmethod
    def create_user(user_id="987654321", screen_name="testuser"):
        """Create a mock user object."""
        user = Mock()
        user.id = user_id
        user.screen_name = screen_name
        user.name = "Test User"
        user.followers_count = 10000
        user.following_count = 500
        return user
    
    @staticmethod
    def create_tweet_list():
        """Create a mock list of tweets."""
        tweets = [
            MockTwikit.create_tweet("1", "$NVDA earnings beat!", 500),
            MockTwikit.create_tweet("2", "AI stocks rally today", 300),
            MockTwikit.create_tweet("3", "$AMD new product launch", 200)
        ]
        
        # Make it iterable and add a next() method
        mock_list = Mock()
        mock_list.__iter__ = lambda self: iter(tweets)
        mock_list.__len__ = lambda self: len(tweets)
        mock_list.next = AsyncMock(side_effect=Exception("No more tweets"))
        
        return mock_list
    
    @staticmethod
    def create_client():
        """Create a mock twikit Client."""
        client = Mock()
        
        # Mock login
        client.login = AsyncMock(return_value=True)
        
        # Mock load_cookies
        client.load_cookies = Mock()
        
        # Mock save_cookies
        client.save_cookies = Mock()
        
        # Mock search_tweet
        async def mock_search_tweet(query, product='Top'):
            return MockTwikit.create_tweet_list()
        
        client.search_tweet = AsyncMock(side_effect=mock_search_tweet)
        
        # Mock get_user_by_screen_name
        async def mock_get_user(screen_name):
            return MockTwikit.create_user(screen_name=screen_name)
        
        client.get_user_by_screen_name = AsyncMock(side_effect=mock_get_user)
        
        # Mock get_user_tweets
        async def mock_get_user_tweets(user_id, tweet_type):
            return MockTwikit.create_tweet_list()
        
        client.get_user_tweets = AsyncMock(side_effect=mock_get_user_tweets)
        
        # Mock get_tweet_by_id
        async def mock_get_tweet(tweet_id):
            tweet = MockTwikit.create_tweet(tweet_id=tweet_id)
            tweet.get_replies = AsyncMock(return_value=[
                MockTwikit.create_tweet("reply1", "Great tweet!", 50),
                MockTwikit.create_tweet("reply2", "I agree!", 25)
            ])
            return tweet
        
        client.get_tweet_by_id = AsyncMock(side_effect=mock_get_tweet)
        
        return client
