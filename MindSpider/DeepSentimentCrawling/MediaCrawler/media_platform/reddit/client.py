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
Reddit Client Module

Provides Reddit API client using PRAW library for scraping.
Follows the same pattern as other MediaCrawler platform clients.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from loguru import logger

from .field import RedditSortType, RedditTimeFilter

# Import PRAW with graceful fallback
try:
    import praw
    from praw.models import Submission, Comment
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    praw = None
    logger.warning("praw not installed. Run `pip install praw` to enable Reddit scraping.")


class RedditClient:
    """
    Reddit API Client using PRAW (official API).
    
    Uses the official Reddit API with a generous free tier
    (100 requests/minute) for searching and monitoring.
    
    Features:
    - Search posts across subreddits
    - Get hot/new/top posts
    - Fetch post comments
    - Financial subreddit focus
    
    Usage:
        client = RedditClient(
            client_id="your_client_id",
            client_secret="your_client_secret"
        )
        posts = client.search_posts("NVDA earnings", limit=100)
    """
    
    # Default subreddits for Trade & Investment
    FINANCE_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options", "stockmarket"]
    TECH_SUBREDDITS = ["technology", "nvidia", "AMD_Stock", "artificial", "MachineLearning"]
    
    def __init__(
        self,
        timeout: int = 60,
        proxy: Optional[str] = None,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit client.
        
        Args:
            timeout: Request timeout in seconds
            proxy: Optional proxy URL (not used by PRAW directly)
            client_id: Reddit app client ID (or from REDDIT_CLIENT_ID env var)
            client_secret: Reddit app client secret (or from REDDIT_CLIENT_SECRET env var)
            user_agent: Custom user agent (or from REDDIT_USER_AGENT env var)
        """
        if not PRAW_AVAILABLE:
            raise ImportError("praw library not installed. Run: pip install praw")
        
        self.timeout = timeout
        self.proxy = proxy
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "BettaFish/1.0 Trade Investment Monitor")
        
        self._reddit = None
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Initialize Reddit client if not already done."""
        if self._initialized:
            return True
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("[RedditClient] Reddit credentials not provided.")
            return False
        
        try:
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self._initialized = True
            logger.info("[RedditClient] Initialized Reddit client")
            return True
        except Exception as e:
            logger.error(f"[RedditClient] Initialization failed: {e}")
            return False
    
    def search_posts(
        self,
        keyword: str,
        subreddits: Optional[List[str]] = None,
        sort: RedditSortType = RedditSortType.RELEVANCE,
        time_filter: RedditTimeFilter = RedditTimeFilter.WEEK,
        limit: int = 100,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Search posts across subreddits.
        
        Args:
            keyword: Search query
            subreddits: List of subreddits to search (default: finance + tech)
            sort: Sort order for results
            time_filter: Time filter for results
            limit: Maximum number of posts
            callback: Optional callback for processing posts
        
        Returns:
            List of post dictionaries
        """
        if not self._ensure_initialized():
            logger.error("[RedditClient] Not initialized, cannot search")
            return []
        
        results = []
        try:
            subreddits = subreddits or (self.FINANCE_SUBREDDITS + self.TECH_SUBREDDITS)
            subreddit_str = "+".join(subreddits)
            
            submissions = self._reddit.subreddit(subreddit_str).search(
                keyword,
                sort=sort.value,
                time_filter=time_filter.value,
                limit=limit
            )
            
            for submission in submissions:
                post_data = self._parse_submission(submission)
                results.append(post_data)
                
                if callback:
                    callback(post_data)
            
            logger.info(f"[RedditClient] Found {len(results)} posts for '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"[RedditClient] Search failed: {e}")
            return results
    
    def get_hot_posts(
        self,
        subreddit: str,
        limit: int = 100,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Get hot/trending posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum number of posts
            callback: Optional callback
        
        Returns:
            List of post dictionaries
        """
        if not self._ensure_initialized():
            return []
        
        results = []
        try:
            submissions = self._reddit.subreddit(subreddit).hot(limit=limit)
            
            for submission in submissions:
                post_data = self._parse_submission(submission)
                results.append(post_data)
                
                if callback:
                    callback(post_data)
            
            logger.info(f"[RedditClient] Got {len(results)} hot posts from r/{subreddit}")
            return results
            
        except Exception as e:
            logger.error(f"[RedditClient] Get hot posts failed: {e}")
            return results
    
    def get_new_posts(
        self,
        subreddit: str,
        limit: int = 100,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Get newest posts from a subreddit.
        
        Args:
            subreddit: Subreddit name
            limit: Maximum number of posts
            callback: Optional callback
        
        Returns:
            List of post dictionaries
        """
        if not self._ensure_initialized():
            return []
        
        results = []
        try:
            submissions = self._reddit.subreddit(subreddit).new(limit=limit)
            
            for submission in submissions:
                post_data = self._parse_submission(submission)
                results.append(post_data)
                
                if callback:
                    callback(post_data)
            
            logger.info(f"[RedditClient] Got {len(results)} new posts from r/{subreddit}")
            return results
            
        except Exception as e:
            logger.error(f"[RedditClient] Get new posts failed: {e}")
            return results
    
    def get_post_comments(
        self,
        post_id: str,
        limit: int = 100,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Get comments from a specific post.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments
            callback: Optional callback
        
        Returns:
            List of comment dictionaries
        """
        if not self._ensure_initialized():
            return []
        
        results = []
        try:
            submission = self._reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Flatten tree
            
            for comment in submission.comments.list()[:limit]:
                comment_data = self._parse_comment(comment)
                results.append(comment_data)
                
                if callback:
                    callback(comment_data)
            
            logger.info(f"[RedditClient] Got {len(results)} comments for post {post_id}")
            return results
            
        except Exception as e:
            logger.error(f"[RedditClient] Get comments failed: {e}")
            return results
    
    def _parse_submission(self, submission: 'Submission') -> Dict[str, Any]:
        """Parse PRAW submission into dictionary."""
        created_dt = datetime.utcfromtimestamp(submission.created_utc) if submission.created_utc else None
        
        return {
            "post_id": submission.id,
            "title": submission.title,
            "text": submission.selftext[:2000] if submission.selftext else "",
            "subreddit": str(submission.subreddit),
            "author": str(submission.author) if submission.author else "[deleted]",
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "created_at": created_dt.isoformat() if created_dt else None,
            "url": submission.url,
            "permalink": f"https://reddit.com{submission.permalink}",
            "is_self": submission.is_self,
            "flair": submission.link_flair_text,
            "awards": getattr(submission, 'total_awards_received', 0)
        }
    
    def _parse_comment(self, comment: 'Comment') -> Dict[str, Any]:
        """Parse PRAW comment into dictionary."""
        created_dt = datetime.utcfromtimestamp(comment.created_utc) if comment.created_utc else None
        
        return {
            "comment_id": comment.id,
            "body": comment.body[:1000] if comment.body else "",
            "author": str(comment.author) if comment.author else "[deleted]",
            "score": comment.score,
            "created_utc": comment.created_utc,
            "created_at": created_dt.isoformat() if created_dt else None,
            "parent_id": comment.parent_id,
            "is_submitter": comment.is_submitter
        }
