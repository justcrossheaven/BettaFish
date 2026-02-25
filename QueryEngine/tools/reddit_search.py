"""
Reddit Search Tools for Trade & Investment Analysis

Version: 1.0
Last Updated: 2026-01-30

This module provides Reddit search capabilities using the PRAW library
(official Reddit API) for monitoring financial discussions.

Key Features:
- Search posts across multiple subreddits
- Get hot/trending posts from specific subreddits
- Get post comments with sentiment context
- Focus on financial/tech subreddits

Cost: $0 (free tier: 100 requests/minute)
"""

import os
import sys
import time
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

# Import PRAW with graceful fallback
try:
    import praw
    from praw.models import Submission, Comment
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("praw not installed. Run `pip install praw` to enable Reddit search.")


# --- 1. Data Structure Definitions ---

@dataclass
class RedditPost:
    """
    Reddit post/submission data structure.
    Contains essential fields for Trade & Investment analysis.
    """
    id: str
    title: str
    text: str
    subreddit: str
    author: Optional[str] = None
    score: int = 0
    upvote_ratio: float = 0.0
    num_comments: int = 0
    created_utc: Optional[float] = None
    created_at: Optional[str] = None
    url: str = ""
    permalink: str = ""
    is_self: bool = True
    flair: Optional[str] = None
    mentioned_tickers: List[str] = field(default_factory=list)
    awards_count: int = 0


@dataclass
class RedditComment:
    """Reddit comment data structure."""
    id: str
    body: str
    author: Optional[str] = None
    score: int = 0
    created_utc: Optional[float] = None
    created_at: Optional[str] = None
    parent_id: Optional[str] = None
    is_submitter: bool = False
    mentioned_tickers: List[str] = field(default_factory=list)


@dataclass
class RedditResponse:
    """
    Encapsulates Reddit API response for consistent interface.
    """
    query: str
    subreddits: List[str] = field(default_factory=list)
    posts: List[RedditPost] = field(default_factory=list)
    comments: List[RedditComment] = field(default_factory=list)
    response_time: Optional[float] = None
    error: Optional[str] = None


# --- 2. Helper Functions ---

def extract_tickers(text: str) -> List[str]:
    """Extract stock tickers (e.g., $NVDA, NVDA) from text."""
    import re
    # Match both $TICKER and standalone uppercase tickers
    ticker_pattern = r'\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b'
    matches = re.findall(ticker_pattern, text.upper())
    tickers = []
    for match in matches:
        ticker = match[0] or match[1]
        # Filter out common words that look like tickers
        if ticker not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL',
                         'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS',
                         'HAVE', 'BEEN', 'FROM', 'WILL', 'THIS', 'THAT', 'WHAT',
                         'THEY', 'WITH', 'JUST', 'YOUR', 'ABOUT', 'INTO', 'LIKE',
                         'DD', 'WSB', 'ETF', 'IPO', 'CEO', 'CFO', 'SEC', 'FDA',
                         'AI', 'EV', 'ER', 'GDP', 'ATH', 'EOD', 'EOW', 'IMO']:
            tickers.append(ticker)
    return list(set(tickers))


def parse_submission(submission: 'Submission') -> RedditPost:
    """Parse PRAW submission object into RedditPost dataclass."""
    text = submission.selftext if hasattr(submission, 'selftext') else ''
    full_text = f"{submission.title} {text}"
    
    created_dt = datetime.utcfromtimestamp(submission.created_utc) if submission.created_utc else None
    
    return RedditPost(
        id=submission.id,
        title=submission.title,
        text=text[:2000],  # Limit text length
        subreddit=str(submission.subreddit),
        author=str(submission.author) if submission.author else '[deleted]',
        score=submission.score,
        upvote_ratio=submission.upvote_ratio,
        num_comments=submission.num_comments,
        created_utc=submission.created_utc,
        created_at=created_dt.isoformat() if created_dt else None,
        url=submission.url,
        permalink=f"https://reddit.com{submission.permalink}",
        is_self=submission.is_self,
        flair=submission.link_flair_text,
        mentioned_tickers=extract_tickers(full_text),
        awards_count=getattr(submission, 'total_awards_received', 0)
    )


def parse_comment(comment: 'Comment') -> RedditComment:
    """Parse PRAW comment object into RedditComment dataclass."""
    body = comment.body if hasattr(comment, 'body') else ''
    created_dt = datetime.utcfromtimestamp(comment.created_utc) if comment.created_utc else None
    
    return RedditComment(
        id=comment.id,
        body=body[:1000],  # Limit body length
        author=str(comment.author) if comment.author else '[deleted]',
        score=comment.score,
        created_utc=comment.created_utc,
        created_at=created_dt.isoformat() if created_dt else None,
        parent_id=comment.parent_id,
        is_submitter=comment.is_submitter,
        mentioned_tickers=extract_tickers(body)
    )


# --- 3. Reddit Search Client ---

class RedditSearchClient:
    """
    Reddit search client using official PRAW library.
    
    This client uses the official Reddit API with a generous free tier
    (100 requests/minute) for searching and monitoring subreddits.
    
    Features:
    - Search posts across multiple subreddits
    - Get hot/new/top posts from specific subreddits
    - Get comments from posts
    - Financial/tech subreddit focus
    
    Usage:
        client = RedditSearchClient()
        results = client.search_posts("NVDA earnings")
        hot_posts = client.get_hot_posts("wallstreetbets", limit=10)
    """
    
    # Default subreddits for Trade & Investment focus
    FINANCE_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options", "stockmarket"]
    TECH_SUBREDDITS = ["technology", "nvidia", "AMD_Stock", "artificial", "MachineLearning"]
    ALL_DEFAULT_SUBREDDITS = FINANCE_SUBREDDITS + TECH_SUBREDDITS
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit app client ID (or from REDDIT_CLIENT_ID env var)
            client_secret: Reddit app client secret (or from REDDIT_CLIENT_SECRET env var)
            user_agent: Custom user agent (or from REDDIT_USER_AGENT env var)
        """
        if not PRAW_AVAILABLE:
            raise ImportError("praw library not installed. Run: pip install praw")
        
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
            logger.warning("[RedditSearchClient] Reddit credentials not provided. "
                          "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env vars.")
            return False
        
        try:
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self._initialized = True
            logger.info("[RedditSearchClient] Initialized Reddit client")
            return True
        except Exception as e:
            logger.error(f"[RedditSearchClient] Initialization failed: {e}")
            return False
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
    def search_posts(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 25
    ) -> RedditResponse:
        """
        【Tool】Search Posts: Search Reddit posts across subreddits.
        
        Designed for AI Agent use - simple interface with smart defaults.
        
        Args:
            query: Search query (supports ticker symbols like $NVDA)
            subreddits: List of subreddits to search (default: finance + tech)
            sort: Sort order - 'relevance', 'hot', 'top', 'new', 'comments'
            time_filter: Time filter - 'hour', 'day', 'week', 'month', 'year', 'all'
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with list of RedditPost objects
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit Search (query: {query}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=query,
                error="Reddit client not initialized. Check credentials."
            )
        
        try:
            subreddits = subreddits or self.ALL_DEFAULT_SUBREDDITS
            subreddit_str = "+".join(subreddits)
            
            submissions = self._reddit.subreddit(subreddit_str).search(
                query,
                sort=sort,
                time_filter=time_filter,
                limit=limit
            )
            
            posts = []
            for submission in submissions:
                posts.append(parse_submission(submission))
            
            return RedditResponse(
                query=query,
                subreddits=subreddits,
                posts=posts,
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[RedditSearchClient] Search failed: {e}")
            return RedditResponse(
                query=query,
                subreddits=subreddits or [],
                error=str(e),
                response_time=time.time() - start_time
            )
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
    def get_hot_posts(
        self,
        subreddit: str,
        limit: int = 25
    ) -> RedditResponse:
        """
        【Tool】Get Hot Posts: Get trending posts from a specific subreddit.
        
        Useful for monitoring what's currently popular in finance/tech communities.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with hot posts from the subreddit
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit Hot Posts (subreddit: r/{subreddit}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=f"hot:r/{subreddit}",
                error="Reddit client not initialized. Check credentials."
            )
        
        try:
            submissions = self._reddit.subreddit(subreddit).hot(limit=limit)
            
            posts = []
            for submission in submissions:
                posts.append(parse_submission(submission))
            
            return RedditResponse(
                query=f"hot:r/{subreddit}",
                subreddits=[subreddit],
                posts=posts,
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[RedditSearchClient] Get hot posts failed: {e}")
            return RedditResponse(
                query=f"hot:r/{subreddit}",
                subreddits=[subreddit],
                error=str(e),
                response_time=time.time() - start_time
            )
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
    def get_new_posts(
        self,
        subreddit: str,
        limit: int = 25
    ) -> RedditResponse:
        """
        【Tool】Get New Posts: Get newest posts from a specific subreddit.
        
        Useful for catching breaking news and discussions early.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with newest posts from the subreddit
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit New Posts (subreddit: r/{subreddit}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=f"new:r/{subreddit}",
                error="Reddit client not initialized. Check credentials."
            )
        
        try:
            submissions = self._reddit.subreddit(subreddit).new(limit=limit)
            
            posts = []
            for submission in submissions:
                posts.append(parse_submission(submission))
            
            return RedditResponse(
                query=f"new:r/{subreddit}",
                subreddits=[subreddit],
                posts=posts,
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[RedditSearchClient] Get new posts failed: {e}")
            return RedditResponse(
                query=f"new:r/{subreddit}",
                subreddits=[subreddit],
                error=str(e),
                response_time=time.time() - start_time
            )
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
    def search_by_ticker(
        self,
        ticker: str,
        limit: int = 25
    ) -> RedditResponse:
        """
        【Tool】Search by Ticker: Search posts mentioning a specific stock ticker.
        
        Optimized for financial sentiment analysis.
        
        Args:
            ticker: Stock ticker symbol (e.g., "NVDA", "AMD")
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with posts mentioning the ticker
        """
        ticker_query = ticker.upper()
        # Search with both $TICKER and plain TICKER formats
        query = f"${ticker_query} OR {ticker_query}"
        logger.info(f"--- TOOL: Reddit Ticker Search (ticker: {ticker_query}) ---")
        
        return self.search_posts(
            query=query,
            subreddits=self.FINANCE_SUBREDDITS,
            sort="new",
            time_filter="week",
            limit=limit
        )
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
    def get_post_comments(
        self,
        post_id: str,
        limit: int = 50
    ) -> RedditResponse:
        """
        【Tool】Get Post Comments: Get comments from a specific post.
        
        Useful for deep-diving into discussions.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to return
        
        Returns:
            RedditResponse with comments from the post
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit Post Comments (post_id: {post_id}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=f"comments:{post_id}",
                error="Reddit client not initialized. Check credentials."
            )
        
        try:
            submission = self._reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Flatten comment tree
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                comments.append(parse_comment(comment))
            
            return RedditResponse(
                query=f"comments:{post_id}",
                posts=[parse_submission(submission)],
                comments=comments,
                response_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"[RedditSearchClient] Get comments failed: {e}")
            return RedditResponse(
                query=f"comments:{post_id}",
                error=str(e),
                response_time=time.time() - start_time
            )


# --- 4. Utility Functions ---

def print_reddit_response(response: RedditResponse):
    """Print Reddit response summary for testing."""
    if response.error:
        print(f"Error: {response.error}")
        return
    
    print(f"\nQuery: '{response.query}' | Time: {response.response_time:.2f}s")
    print(f"Subreddits: {', '.join(response.subreddits)}")
    print(f"Found {len(response.posts)} posts, {len(response.comments)} comments")
    
    for i, post in enumerate(response.posts[:5], 1):
        tickers = ', '.join(post.mentioned_tickers[:5]) if post.mentioned_tickers else 'None'
        print(f"\n{i}. r/{post.subreddit}: {post.title[:80]}...")
        print(f"   ↑{post.score} | 💬{post.num_comments} | Tickers: {tickers}")
        print(f"   {post.permalink}")
    print("-" * 60)


# --- 5. Test & Example Usage ---

if __name__ == "__main__":
    def test_reddit_client():
        """Test the Reddit client with sample queries."""
        try:
            client = RedditSearchClient()
            
            # Test 1: Search for NVIDIA posts
            print("\n=== Test 1: Search NVDA posts ===")
            response = client.search_posts("NVDA earnings", limit=5)
            print_reddit_response(response)
            
            # Test 2: Get hot posts from wallstreetbets
            print("\n=== Test 2: Hot posts from r/wallstreetbets ===")
            response = client.get_hot_posts("wallstreetbets", limit=5)
            print_reddit_response(response)
            
            # Test 3: Search by ticker
            print("\n=== Test 3: Search by ticker AMD ===")
            response = client.search_by_ticker("AMD", limit=5)
            print_reddit_response(response)
            
        except ImportError as e:
            print(f"Import error: {e}")
            print("Please install praw: pip install praw")
        except Exception as e:
            print(f"Test failed: {e}")
            print("Make sure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set.")
    
    # Run test
    test_reddit_client()
