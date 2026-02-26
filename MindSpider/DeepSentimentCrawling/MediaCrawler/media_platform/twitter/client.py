# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""
Twitter/X Client Module

Provides Twitter API client using twikit library for scraping.
Follows the same pattern as the Douyin client.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from loguru import logger

from .field import TwitterSearchType, TwitterSortType

# Import twikit with graceful fallback
try:
    import twikit
    from twikit import Client as TwikitClient
    TWIKIT_AVAILABLE = True
except ImportError:
    TWIKIT_AVAILABLE = False
    TwikitClient = None
    logger.warning("twikit not installed. Run `pip install twikit` to enable Twitter scraping.")


class TwitterClient:
    """
    Twitter/X API Client using twikit (reverse-engineered internal API).
    
    This client simulates the Twitter web interface to fetch data
    without requiring expensive official API access.
    
    Features:
    - Cookie-based authentication with persistence
    - Search tweets with multiple sort options
    - Get user timelines
    - Fetch tweet comments/replies
    
    Usage:
        client = TwitterClient(
            username="your_username",
            email="your_email",
            password="your_password"
        )
        await client.login()
        tweets = await client.search_tweets("$NVDA", limit=100)
    """
    
    def __init__(
        self,
        timeout: int = 60,
        proxy: Optional[str] = None,
        *,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        cookies_path: Optional[str] = None
    ):
        """
        Initialize Twitter client.
        
        Args:
            timeout: Request timeout in seconds
            proxy: Optional proxy URL
            username: Twitter username (or from TWITTER_USERNAME env var)
            email: Twitter email (or from TWITTER_EMAIL env var)
            password: Twitter password (or from TWITTER_PASSWORD env var)
            cookies_path: Path to save/load cookies
        """
        if not TWIKIT_AVAILABLE:
            raise ImportError("twikit library not installed. Run: pip install twikit")
        
        self.timeout = timeout
        self.proxy = proxy
        self.username = username or os.getenv("TWITTER_USERNAME")
        self.email = email or os.getenv("TWITTER_EMAIL")
        self.password = password or os.getenv("TWITTER_PASSWORD")
        self.cookies_path = cookies_path or os.getenv("TWITTER_COOKIES_PATH", "twitter_cookies.json")
        
        # Initialize twikit client
        self._client = TwikitClient('en-US')
        self._logged_in = False
    
    async def login(self) -> bool:
        """
        Login to Twitter.
        Tries to load cookies first, falls back to credential login.
        
        Returns:
            bool: True if login successful
        """
        if self._logged_in:
            return True
        
        # Try to load existing cookies
        cookies_file = Path(self.cookies_path)
        if cookies_file.exists():
            try:
                self._client.load_cookies(str(cookies_file))
                logger.info(f"[TwitterClient] Loaded cookies from {self.cookies_path}")
                self._logged_in = True
                return True
            except Exception as e:
                logger.warning(f"[TwitterClient] Failed to load cookies: {e}")
        
        # Fall back to credential login
        if not all([self.username, self.email, self.password]):
            logger.error("[TwitterClient] Twitter credentials not provided.")
            return False
        
        try:
            await self._client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password
            )
            # Save cookies for future use
            self._client.save_cookies(str(cookies_file))
            logger.info(f"[TwitterClient] Logged in and saved cookies")
            self._logged_in = True
            return True
        except Exception as e:
            logger.error(f"[TwitterClient] Login failed: {e}")
            return False
    
    async def search_tweets(
        self,
        keyword: str,
        search_type: TwitterSearchType = TwitterSearchType.TOP,
        limit: int = 100,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Search tweets by keyword.
        
        Args:
            keyword: Search query
            search_type: Type of search results
            limit: Maximum number of tweets to fetch
            crawl_interval: Delay between pagination requests
            callback: Optional callback for processing tweets
        
        Returns:
            List of tweet dictionaries
        """
        if not await self.login():
            logger.error("[TwitterClient] Not logged in, cannot search")
            return []
        
        results = []
        try:
            tweets = await self._client.search_tweet(keyword, product=search_type.value)
            
            while tweets and len(results) < limit:
                for tweet in tweets:
                    if len(results) >= limit:
                        break
                    
                    tweet_data = self._parse_tweet(tweet)
                    results.append(tweet_data)
                    
                    if callback:
                        await callback(tweet_data)
                
                # Pagination
                if len(results) < limit:
                    await asyncio.sleep(crawl_interval)
                    try:
                        tweets = await tweets.next()
                    except Exception:
                        break
            
            logger.info(f"[TwitterClient] Found {len(results)} tweets for '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"[TwitterClient] Search failed: {e}")
            return results
    
    async def get_user_tweets(
        self,
        screen_name: str,
        tweet_type: TwitterSortType = TwitterSortType.TWEETS,
        limit: int = 100,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Get tweets from a specific user.
        
        Args:
            screen_name: Twitter username (without @)
            tweet_type: Type of tweets to fetch
            limit: Maximum number of tweets
            crawl_interval: Delay between requests
            callback: Optional callback for processing
        
        Returns:
            List of tweet dictionaries
        """
        if not await self.login():
            logger.error("[TwitterClient] Not logged in, cannot get user tweets")
            return []
        
        results = []
        try:
            user = await self._client.get_user_by_screen_name(screen_name)
            tweets = await self._client.get_user_tweets(user.id, tweet_type.value)
            
            while tweets and len(results) < limit:
                for tweet in tweets:
                    if len(results) >= limit:
                        break
                    
                    tweet_data = self._parse_tweet(tweet)
                    results.append(tweet_data)
                    
                    if callback:
                        await callback(tweet_data)
                
                if len(results) < limit:
                    await asyncio.sleep(crawl_interval)
                    try:
                        tweets = await tweets.next()
                    except Exception:
                        break
            
            logger.info(f"[TwitterClient] Got {len(results)} tweets from @{screen_name}")
            return results
            
        except Exception as e:
            logger.error(f"[TwitterClient] Get user tweets failed: {e}")
            return results
    
    async def get_tweet_replies(
        self,
        tweet_id: str,
        limit: int = 50,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Get replies to a specific tweet.
        
        Args:
            tweet_id: Tweet ID to get replies for
            limit: Maximum number of replies
            crawl_interval: Delay between requests
            callback: Optional callback
        
        Returns:
            List of reply dictionaries
        """
        if not await self.login():
            return []
        
        results = []
        try:
            tweet = await self._client.get_tweet_by_id(tweet_id)
            replies = await tweet.get_replies()
            
            for reply in replies[:limit]:
                reply_data = self._parse_tweet(reply)
                results.append(reply_data)
                
                if callback:
                    await callback(reply_data)
            
            return results
            
        except Exception as e:
            logger.error(f"[TwitterClient] Get replies failed: {e}")
            return results
    
    def _parse_tweet(self, tweet) -> Dict[str, Any]:
        """Parse twikit tweet object into dictionary."""
        user = getattr(tweet, 'user', None)
        
        return {
            "tweet_id": str(getattr(tweet, 'id', '')),
            "text": getattr(tweet, 'text', ''),
            "created_at": str(getattr(tweet, 'created_at', '')),
            "user_id": str(getattr(user, 'id', '')) if user else None,
            "user_name": getattr(user, 'name', None) if user else None,
            "user_screen_name": getattr(user, 'screen_name', None) if user else None,
            "user_followers": getattr(user, 'followers_count', 0) if user else 0,
            "retweet_count": getattr(tweet, 'retweet_count', 0),
            "favorite_count": getattr(tweet, 'favorite_count', 0),
            "reply_count": getattr(tweet, 'reply_count', 0),
            "quote_count": getattr(tweet, 'quote_count', 0),
            "view_count": getattr(tweet, 'view_count', None),
            "is_retweet": getattr(tweet, 'is_retweet', False),
            "hashtags": [h.get('text', '') for h in getattr(tweet, 'hashtags', []) or []],
            "url": f"https://twitter.com/i/status/{getattr(tweet, 'id', '')}"
        }
