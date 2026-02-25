"""
Prompts package for BettaFish Trade & Investment Analysis.

This package contains shared prompt resources including:
- financial_terminology: Financial terms, search patterns, and sector-specific vocabulary
"""

from .financial_terminology import (
    FINANCIAL_SEARCH_TERMS,
    KEY_METRICS,
    TECH_SECTOR_COMPANIES,
    TECH_TICKER_LIST,
    FINANCIAL_EVENTS,
    FINANCIAL_DATA_SOURCES,
    SENTIMENT_SIGNALS,
    DEFAULT_ANALYSIS_FOCUS
)

__all__ = [
    'FINANCIAL_SEARCH_TERMS',
    'KEY_METRICS',
    'TECH_SECTOR_COMPANIES',
    'TECH_TICKER_LIST',
    'FINANCIAL_EVENTS',
    'FINANCIAL_DATA_SOURCES',
    'SENTIMENT_SIGNALS',
    'DEFAULT_ANALYSIS_FOCUS'
]
