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
Reddit Enum Field Definitions

Defines enumerations for Reddit sort types and time filters.
"""

from enum import Enum


class RedditSortType(str, Enum):
    """Reddit post sort types."""
    HOT = "hot"               # Hot/trending posts
    NEW = "new"               # Newest posts
    TOP = "top"               # Top rated posts
    RISING = "rising"         # Rising posts
    CONTROVERSIAL = "controversial"  # Controversial posts
    RELEVANCE = "relevance"   # Most relevant (for search)
    COMMENTS = "comments"     # Most comments (for search)


class RedditTimeFilter(str, Enum):
    """Reddit time filter options."""
    HOUR = "hour"     # Past hour
    DAY = "day"       # Past 24 hours
    WEEK = "week"     # Past week
    MONTH = "month"   # Past month
    YEAR = "year"     # Past year
    ALL = "all"       # All time
