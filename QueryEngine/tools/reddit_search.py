"""
Reddit Search Tools for Trade & Investment Analysis

Version: 1.1
Last Updated: 2026-02-26

This module provides Reddit search capabilities using:
1. PRAW library (official API) when credentials are available (100 req/min)
2. Reddit's public JSON API as fallback (no auth needed, 60 req/min)

Key Features:
- Search posts across multiple subreddits
- Get hot/trending posts from specific subreddits
- Get post comments with sentiment context
- Focus on financial/tech subreddits
- Automatic fallback when credentials not available

Cost: $0 (free tier)
"""

import os
import sys
import time
import requests
from typing import List, Optional, Dict, Any
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


# --- JSON API Fallback Functions ---

def parse_json_submission(post_data: Dict[str, Any]) -> RedditPost:
    """Parse Reddit JSON API submission into RedditPost dataclass."""
    data = post_data.get('data', {})
    
    title = data.get('title', '')
    text = data.get('selftext', '')
    full_text = f"{title} {text}"
    
    created_utc = data.get('created_utc')
    created_dt = datetime.utcfromtimestamp(created_utc) if created_utc else None
    
    return RedditPost(
        id=data.get('id', ''),
        title=title,
        text=text[:2000],
        subreddit=data.get('subreddit', ''),
        author=data.get('author', '[deleted]'),
        score=data.get('score', 0),
        upvote_ratio=data.get('upvote_ratio', 0.0),
        num_comments=data.get('num_comments', 0),
        created_utc=created_utc,
        created_at=created_dt.isoformat() if created_dt else None,
        url=data.get('url', ''),
        permalink=f"https://reddit.com{data.get('permalink', '')}",
        is_self=data.get('is_self', True),
        flair=data.get('link_flair_text'),
        mentioned_tickers=extract_tickers(full_text),
        awards_count=data.get('total_awards_received', 0)
    )


def fetch_reddit_json(url: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
    """
    Fetch data from Reddit's public JSON API.
    
    Args:
        url: Reddit URL (will append .json if not present)
        params: Query parameters
        timeout: Request timeout
    
    Returns:
        JSON response or None on error
    """
    if not url.endswith('.json'):
        url = url.rstrip('/') + '.json'
    
    headers = {
        'User-Agent': 'BettaFish/1.1 Trade Investment Monitor (Public API)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[RedditJSON] Request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"[RedditJSON] Parse failed: {e}")
        return None


# --- 3. Reddit Search Client ---

class RedditSearchClient:
    """
    Reddit search client with dual-mode support:
    1. PRAW (official API) when credentials available - 100 req/min, better features
    2. Public JSON API fallback (no auth) - 60 req/min, limited features
    
    Automatically falls back to JSON API when credentials not available.
    
    Features:
    - Search posts across multiple subreddits
    - Get hot/new/top posts from specific subreddits
    - Get comments from posts (PRAW only)
    - Financial/tech subreddit focus
    
    Usage:
        # With credentials
        client = RedditSearchClient()  # Uses PRAW if REDDIT_CLIENT_ID set
        
        # Without credentials (JSON API fallback)
        client = RedditSearchClient()  # Auto-fallback to public API
        
        results = client.search_posts("NVDA earnings")
        hot_posts = client.get_hot_posts("wallstreetbets", limit=10)
    """
    
    # Default subreddits for Trade & Investment focus
    FINANCE_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options", "stockmarket", "SecurityAnalysis"]
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
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "BettaFish/1.1 Trade Investment Monitor")
        
        self._reddit = None
        self._initialized = False
        self._use_praw = PRAW_AVAILABLE and bool(self.client_id) and bool(self.client_secret)
        
        if self._use_praw:
            logger.info("[RedditSearchClient] PRAW mode enabled (credentials found)")
        else:
            logger.info("[RedditSearchClient] JSON API fallback mode (no credentials or PRAW not installed)")
    
    def _ensure_initialized(self) -> bool:
        """Initialize Reddit client if not already done."""
        if self._initialized:
            return True
        
        if not self._use_praw:
            # JSON API doesn't need initialization
            self._initialized = True
            return True
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("[RedditSearchClient] Reddit credentials not provided. "
                          "Falling back to JSON API.")
            self._use_praw = False
            self._initialized = True
            return True
        
        try:
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self._initialized = True
            logger.info("[RedditSearchClient] Initialized PRAW client")
            return True
        except Exception as e:
            logger.error(f"[RedditSearchClient] PRAW initialization failed: {e}. Falling back to JSON API.")
            self._use_praw = False
            self._initialized = True
            return True
    
    def _search_posts_json(
        self,
        query: str,
        subreddits: List[str],
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 25
    ) -> List[RedditPost]:
        """Search posts using Reddit's public JSON API (no auth required)."""
        posts = []
        
        for subreddit in subreddits[:5]:  # Limit to avoid too many requests
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': query,
                    'sort': 'new' if sort == 'relevance' else sort,  # JSON API doesn't support 'relevance'
                    't': time_filter,
                    'limit': min(limit, 100),  # Reddit API limit
                    'restrict_sr': 'on'  # Search within subreddit only
                }
                
                logger.debug(f"[RedditJSON] Searching r/{subreddit} for '{query}'")
                data = fetch_reddit_json(url, params)
                
                if not data or 'data' not in data:
                    continue
                
                children = data['data'].get('children', [])
                for child in children:
                    if len(posts) >= limit:
                        break
                    try:
                        post = parse_json_submission(child)
                        posts.append(post)
                    except Exception as e:
                        logger.warning(f"[RedditJSON] Failed to parse post: {e}")
                        continue
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"[RedditJSON] Failed to search r/{subreddit}: {e}")
                continue
        
        return posts
    
    def _get_posts_json(
        self,
        subreddit: str,
        listing: str = "hot",
        limit: int = 25
    ) -> List[RedditPost]:
        """Get posts from a subreddit using JSON API."""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/{listing}.json"
            params = {'limit': min(limit, 100)}
            
            logger.debug(f"[RedditJSON] Getting {listing} posts from r/{subreddit}")
            data = fetch_reddit_json(url, params)
            
            if not data or 'data' not in data:
                return []
            
            posts = []
            children = data['data'].get('children', [])
            for child in children[:limit]:
                try:
                    post = parse_json_submission(child)
                    posts.append(post)
                except Exception as e:
                    logger.warning(f"[RedditJSON] Failed to parse post: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            logger.error(f"[RedditJSON] Failed to get posts: {e}")
            return []
    
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
        Uses PRAW if credentials available, falls back to JSON API.
        
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
        subreddits = subreddits or self.ALL_DEFAULT_SUBREDDITS
        logger.info(f"--- TOOL: Reddit Search (query: {query}, mode: {'PRAW' if self._use_praw else 'JSON'}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=query,
                error="Reddit client initialization failed."
            )
        
        try:
            if self._use_praw:
                # Use PRAW (official API)
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
            else:
                # Use JSON API fallback
                posts = self._search_posts_json(query, subreddits, sort, time_filter, limit)
            
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
        Uses PRAW if available, falls back to JSON API.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with hot posts from the subreddit
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit Hot Posts (subreddit: r/{subreddit}, mode: {'PRAW' if self._use_praw else 'JSON'}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=f"hot:r/{subreddit}",
                error="Reddit client initialization failed."
            )
        
        try:
            if self._use_praw:
                submissions = self._reddit.subreddit(subreddit).hot(limit=limit)
                posts = []
                for submission in submissions:
                    posts.append(parse_submission(submission))
            else:
                posts = self._get_posts_json(subreddit, "hot", limit)
            
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
        Uses PRAW if available, falls back to JSON API.
        
        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum number of posts to return
        
        Returns:
            RedditResponse with newest posts from the subreddit
        """
        start_time = time.time()
        logger.info(f"--- TOOL: Reddit New Posts (subreddit: r/{subreddit}, mode: {'PRAW' if self._use_praw else 'JSON'}) ---")
        
        if not self._ensure_initialized():
            return RedditResponse(
                query=f"new:r/{subreddit}",
                error="Reddit client initialization failed."
            )
        
        try:
            if self._use_praw:
                submissions = self._reddit.subreddit(subreddit).new(limit=limit)
                posts = []
                for submission in submissions:
                    posts.append(parse_submission(submission))
            else:
                posts = self._get_posts_json(subreddit, "new", limit)
            
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
        NOTE: Requires PRAW (credentials). Not available with JSON API.
        
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
                error="Reddit client initialization failed."
            )
        
        if not self._use_praw:
            return RedditResponse(
                query=f"comments:{post_id}",
                error="Comment fetching requires PRAW credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.",
                response_time=time.time() - start_time
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
