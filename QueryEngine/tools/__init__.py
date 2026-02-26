"""
工具调用模块
提供外部工具接口，如网络搜索、基本面分析等
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

# Import fundamental analysis tools from utils
import sys
import os
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

from insider_trading import (
    InsiderTradingParser,
    InsiderTransaction,
    print_insider_summary
)

from institutional_ownership import (
    InstitutionalOwnershipParser,
    InstitutionalPosition,
    PositionChange,
    print_ownership_summary
)

from dcf_model import (
    DCFModel,
    DCFAssumptions,
    DCFScenarioAnalysis,
    print_dcf_results,
    print_scenario_analysis
)

from earnings_calendar import (
    EarningsCalendar,
    EarningsEvent,
    EarningsHistory,
    print_earnings_summary
)

__all__ = [
    # Tavily (existing)
    "TavilyNewsAgency", 
    "SearchResult", 
    "TavilyResponse", 
    "ImageResult",
    "print_response_summary",
    # Twitter
    "TwitterSearchClient",
    "TweetResult",
    "TwitterResponse",
    "print_twitter_response",
    # Reddit
    "RedditSearchClient",
    "RedditPost",
    "RedditComment",
    "RedditResponse",
    "print_reddit_response",
    # Fundamental Analysis Tools (NEW)
    "InsiderTradingParser",
    "InsiderTransaction",
    "print_insider_summary",
    "InstitutionalOwnershipParser",
    "InstitutionalPosition",
    "PositionChange",
    "print_ownership_summary",
    "DCFModel",
    "DCFAssumptions",
    "DCFScenarioAnalysis",
    "print_dcf_results",
    "print_scenario_analysis",
    "EarningsCalendar",
    "EarningsEvent",
    "EarningsHistory",
    "print_earnings_summary"
]

