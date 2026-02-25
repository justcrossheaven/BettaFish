"""
Twitter/X Search Tools for Trade & Investment Analysis

Version: 1.0
Last Updated: 2026-01-30

This module provides Twitter/X search capabilities using the twikit library
(reverse-engineered internal API) to avoid high official API costs.

Key Features:
- Search tweets by query with financial focus
- Get user timelines for influencer monitoring
- Cookie-based authentication with persistence
- Retry logic for robustness

Cost: $0 (uses twikit, no API key needed - requires Twitter account)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add utils directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
utils_dir = os.path.join(root_dir, 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

# Add project root to path for config import
if root_dir not in sys.path:
    sys.path.append(root_dir)

from retry_helper import with_graceful_retry, SEARCH_API_RETRY_CONFIG
from loguru import logger

# Import twikit with graceful fallback
try:
    import twikit
    from twikit import Client as TwikitClient
    TWIKIT_AVAILABLE = True
except ImportError:
    TWIKIT_AVAILABLE = False
    logger.warning("twikit not installed. Run `pip install twikit` to enable Twitter search.")


# --- 1. Data Structure Definitions ---

@dataclass
class TweetResult:
    """
    Tweet data structure for search results.
    Contains essential fields for Trade & Investment analysis.
    """
    id: str
    text: str
    created_at: Optional[str] = None
    user_name: Optional[str] = None
    user_screen_name: Optional[str] = None
    user_followers_count: Optional[int] = None
    retweet_count: Optional[int] = None
    favorite_count: Optional[int] = None
    reply_count: Optional[int] = None
    quote_count: Optional[int] = None
    views_count: Optional[int] = None
    is_retweet: bool = False
    hashtags: List[str] = field(default_factory=list)
    mentioned_tickers: List[str] = field(default_factory=list)
    url: Optional[str] = None
    
    @property
    def author_username(self) -> Optional[str]:
        """Alias for user_screen_name for backward compatibility."""
        return self.user_screen_name
    
    @property
    def like_count(self) -> Optional[int]:
        """Alias for favorite_count for backward compatibility."""
        return self.favorite_count


@dataclass
class TwitterResponse:
    """
    Encapsulates Twitter API response for consistent interface.
    """
    query: str
    results: List[TweetResult] = field(default_factory=list)
    cursor: Optional[str] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    
    @property
    def tweets(self) -> List[TweetResult]:
        """Alias for results to maintain backward compatibility."""
        return self.results


# --- 2. Helper Functions ---

def extract_tickers(text: str) -> List[str]:
    """Extract stock tickers (e.g., $NVDA, $AMD) from tweet text."""
    import re
    # Handle case where text might not be a string
    if not isinstance(text, str):
        if isinstance(text, list):
            text = ' '.join(str(x) for x in text)
        else:
            text = str(text) if text else ''
    ticker_pattern = r'\$([A-Z]{1,5})'
    return list(set(re.findall(ticker_pattern, text.upper())))


def parse_tweet(tweet_obj) -> TweetResult:
    """Parse twikit tweet object into TweetResult dataclass."""
    # Get text and ensure it's a string
    text = getattr(tweet_obj, 'text', '') or ''
    if isinstance(text, list):
        # If text is a list, join it into a string
        text = ' '.join(str(x) for x in text)
    elif not isinstance(text, str):
        text = str(text) if text else ''
    
    user = getattr(tweet_obj, 'user', None)
    
    return TweetResult(
        id=str(getattr(tweet_obj, 'id', '')),
        text=text,
        created_at=str(getattr(tweet_obj, 'created_at', '')) if hasattr(tweet_obj, 'created_at') else None,
        user_name=getattr(user, 'name', None) if user else None,
        user_screen_name=getattr(user, 'screen_name', None) if user else None,
        user_followers_count=getattr(user, 'followers_count', None) if user else None,
        retweet_count=getattr(tweet_obj, 'retweet_count', 0),
        favorite_count=getattr(tweet_obj, 'favorite_count', 0),
        reply_count=getattr(tweet_obj, 'reply_count', 0),
        quote_count=getattr(tweet_obj, 'quote_count', 0),
        views_count=getattr(tweet_obj, 'view_count', None),
        is_retweet=getattr(tweet_obj, 'is_retweet', False),
        hashtags=[h.get('text', '') for h in getattr(tweet_obj, 'hashtags', []) or []],
        mentioned_tickers=extract_tickers(text),
        url=f"https://twitter.com/i/status/{getattr(tweet_obj, 'id', '')}"
    )


# --- 3. Twitter Search Client ---

class TwitterSearchClient:
    """
    Twitter/X search client using twikit (reverse-engineered internal API).
    
    This client simulates the Twitter web interface to perform searches
    without requiring expensive official API access.
    
    Features:
    - Cookie-based authentication with persistence
    - Search tweets by query with multiple sort options
    - Get user timelines
    - Financial/investment focused search patterns
    
    Usage:
        client = TwitterSearchClient()
        # First time: will need login
        await client.initialize()
        results = await client.search_tweets("$NVDA earnings")
    """
    
    # Default lists for Trade & Investment focus
    FINANCE_KEYWORDS = ["earnings", "revenue", "guidance", "stock", "shares", "bullish", "bearish"]
    TECH_TICKERS = ["NVDA", "AMD", "INTC", "MSFT", "GOOGL", "META", "AAPL", "AMZN", "TSLA", "TSM"]
    FINANCE_INFLUENCERS = ["elikilos", "jimcramer", "WallStreetSilv", "unusual_whales"]
    
    def __init__(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        cookies_path: Optional[str] = None
    ):
        """
        Initialize Twitter client.
        
        Args:
            username: Twitter username (or from TWITTER_USERNAME env var)
            email: Twitter email (or from TWITTER_EMAIL env var)
            password: Twitter password (or from TWITTER_PASSWORD env var)
            cookies_path: Path to save/load cookies (or from TWITTER_COOKIES_PATH env var)
        """
        if not TWIKIT_AVAILABLE:
            raise ImportError("twikit library not installed. Run: pip install twikit")
        
        self.username = username or os.getenv("TWITTER_USERNAME")
        self.email = email or os.getenv("TWITTER_EMAIL")
        self.password = password or os.getenv("TWITTER_PASSWORD")
        self.cookies_path = cookies_path or os.getenv("TWITTER_COOKIES_PATH", "twitter_cookies.json")
        
        # Initialize twikit client
        self.client = TwikitClient('en-US')
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize client with authentication.
        Tries to load cookies first, falls back to login if needed.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True
        
        # Try to load existing cookies
        cookies_file = Path(self.cookies_path)
        if cookies_file.exists():
            try:
                self.client.load_cookies(str(cookies_file))
                logger.info(f"[TwitterSearchClient] Loaded cookies from {self.cookies_path}")
                self._initialized = True
                return True
            except Exception as e:
                logger.warning(f"[TwitterSearchClient] Failed to load cookies: {e}")
        
        # Fall back to login
        if not all([self.username, self.email, self.password]):
            logger.error("[TwitterSearchClient] Twitter credentials not provided. "
                        "Set TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD env vars.")
            return False
        
        try:
            await self.client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password
            )
            # Save cookies for future use
            self.client.save_cookies(str(cookies_file))
            logger.info(f"[TwitterSearchClient] Logged in and saved cookies to {self.cookies_path}")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"[TwitterSearchClient] Login failed: {e}")
            return False
    
    async def search_tweets(
        self,
        query: str,
        product: str = 'Top',
        max_results: int = 20
    ) -> TwitterResponse:
        """
        【Tool】Search Tweets: Search Twitter for tweets matching query.
        
        Designed for AI Agent use - simple interface, minimal parameters.
        
        Args:
            query: Search query (supports Twitter search operators like $TICKER)
            product: Search type - 'Top', 'Latest', 'People', 'Photos', 'Videos'
            max_results: Maximum number of tweets to return
        
        Returns:
            TwitterResponse with list of TweetResult objects
        """
        import time
        start_time = time.time()
        
        logger.info(f"--- TOOL: Twitter Search (query: {query}) ---")
        
        if not await self.initialize():
            return TwitterResponse(
                query=query,
                error="Twitter client not initialized. Check credentials."
            )
        
        try:
            tweets = await self.client.search_tweet(query, product=product)
            logger.debug(f"[TwitterSearchClient] search_tweet returned type: {type(tweets)}")
            
            results = []
            try:
                # Try to iterate through tweets
                tweet_list = list(tweets) if tweets else []
                logger.debug(f"[TwitterSearchClient] Got {len(tweet_list)} tweets")
                
                for i, tweet in enumerate(tweet_list[:max_results]):
                    try:
                        logger.debug(f"[TwitterSearchClient] Parsing tweet {i}, type: {type(tweet)}")
                        parsed = parse_tweet(tweet)
                        results.append(parsed)
                    except Exception as parse_error:
                        logger.warning(f"[TwitterSearchClient] Failed to parse tweet {i}: {parse_error}")
                        continue
                        
            except Exception as iter_error:
                logger.error(f"[TwitterSearchClient] Failed to iterate tweets: {iter_error}")
                raise
            
            return TwitterResponse(
                query=query,
                results=results,
                cursor=getattr(tweets, 'cursor', None),
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[TwitterSearchClient] Search failed: {e}")
            logger.exception("Full traceback:")
            return TwitterResponse(
                query=query,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def search_tweets_by_ticker(
        self,
        ticker: str,
        max_results: int = 20
    ) -> TwitterResponse:
        """
        【Tool】Search by Ticker: Search tweets mentioning a specific stock ticker.
        
        Optimized for financial sentiment analysis.
        
        Args:
            ticker: Stock ticker symbol (e.g., "NVDA", "AMD")
            max_results: Maximum number of tweets to return
        
        Returns:
            TwitterResponse with filtered financial tweets
        """
        # Format ticker with $ prefix if not present
        ticker_query = f"${ticker.upper()}" if not ticker.startswith('$') else ticker.upper()
        logger.info(f"--- TOOL: Twitter Ticker Search (ticker: {ticker_query}) ---")
        return await self.search_tweets(ticker_query, product='Latest', max_results=max_results)
    
    async def get_user_tweets(
        self,
        screen_name: str,
        max_results: int = 20
    ) -> TwitterResponse:
        """
        【Tool】Get User Tweets: Get recent tweets from a specific user.
        
        Useful for monitoring financial influencers and analysts.
        
        Args:
            screen_name: Twitter username (without @)
            max_results: Maximum number of tweets to return
        
        Returns:
            TwitterResponse with user's recent tweets
        """
        import time
        start_time = time.time()
        
        logger.info(f"--- TOOL: Twitter User Tweets (user: @{screen_name}) ---")
        
        if not await self.initialize():
            return TwitterResponse(
                query=f"from:{screen_name}",
                error="Twitter client not initialized. Check credentials."
            )
        
        try:
            user = await self.client.get_user_by_screen_name(screen_name)
            tweets = await self.client.get_user_tweets(user.id, 'Tweets')
            
            results = []
            for tweet in tweets[:max_results]:
                results.append(parse_tweet(tweet))
            
            return TwitterResponse(
                query=f"from:{screen_name}",
                results=results,
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[TwitterSearchClient] Get user tweets failed: {e}")
            return TwitterResponse(
                query=f"from:{screen_name}",
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def search_tweets_sync(
        self,
        query: str,
        product: str = 'Top',
        max_results: int = 20
    ) -> TwitterResponse:
        """
        Synchronous wrapper for search_tweets.
        Useful when calling from non-async context.
        """
        return asyncio.run(self.search_tweets(query, product, max_results))
    
    def search_by_ticker_sync(self, ticker: str, max_results: int = 20) -> TwitterResponse:
        """Synchronous wrapper for search_tweets_by_ticker."""
        return asyncio.run(self.search_tweets_by_ticker(ticker, max_results))


# --- 4. Utility Functions ---

def print_twitter_response(response: TwitterResponse):
    """Print Twitter response summary for testing."""
    if response.error:
        print(f"Error: {response.error}")
        return
    
    print(f"\nQuery: '{response.query}' | Time: {response.response_time:.2f}s")
    print(f"Found {len(response.results)} tweets")
    
    for i, tweet in enumerate(response.results[:5], 1):
        tickers = ', '.join(tweet.mentioned_tickers) if tweet.mentioned_tickers else 'None'
        print(f"\n{i}. @{tweet.user_screen_name}: {tweet.text[:100]}...")
        print(f"   ♥ {tweet.favorite_count} | RT {tweet.retweet_count} | Tickers: {tickers}")
    print("-" * 60)


# --- 5. Test & Example Usage ---

if __name__ == "__main__":
    async def test_twitter_client():
        """Test the Twitter client with sample queries."""
        try:
            client = TwitterSearchClient()
            
            # Test 1: Search for NVIDIA tweets
            print("\n=== Test 1: Search $NVDA tweets ===")
            response = await client.search_tweets("$NVDA earnings", max_results=5)
            print_twitter_response(response)
            
            # Test 2: Search by ticker
            print("\n=== Test 2: Search by ticker AMD ===")
            response = await client.search_tweets_by_ticker("AMD", max_results=5)
            print_twitter_response(response)
            
        except ImportError as e:
            print(f"Import error: {e}")
            print("Please install twikit: pip install twikit")
        except Exception as e:
            print(f"Test failed: {e}")
            print("Make sure TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD are set.")
    
    # Run async test
    asyncio.run(test_twitter_client())
