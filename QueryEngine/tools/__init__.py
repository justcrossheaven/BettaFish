"""
工具调用模块
提供外部工具接口，如网络搜索等
"""

from .search import (
    TavilyNewsAgency, 
    SearchResult, 
    TavilyResponse, 
    ImageResult,
    print_response_summary
)

from .twitter_search import (
    TwitterSearchClient,
    TweetResult,
    TwitterResponse,
    print_twitter_response
)

from .reddit_search import (
    RedditSearchClient,
    RedditPost,
    RedditComment,
    RedditResponse,
    print_reddit_response
)

__all__ = [
    # Tavily (existing)
    "TavilyNewsAgency", 
    "SearchResult", 
    "TavilyResponse", 
    "ImageResult",
    "print_response_summary",
    # Twitter (new)
    "TwitterSearchClient",
    "TweetResult",
    "TwitterResponse",
    "print_twitter_response",
    # Reddit (new)
    "RedditSearchClient",
    "RedditPost",
    "RedditComment",
    "RedditResponse",
    "print_reddit_response"
]

