"""
Prompts package for BettaFish Trade & Investment Analysis.

This package contains shared prompt resources including:
- financial_terminology: Financial terms, search patterns, and sector-specific vocabulary
"""

from .financial_terminology import (
    FINANCIAL_SEARCH_TERMS,
    KEY_METRICS,
    ACCOUNTING_RED_FLAGS,
    TECH_SECTOR_COMPANIES,
    TECH_TICKER_LIST,
    MACRO_CONTEXT_TERMS,
    FINANCIAL_DATA_SOURCES
)

__all__ = [
    'FINANCIAL_SEARCH_TERMS',
    'KEY_METRICS',
    'ACCOUNTING_RED_FLAGS',
    'TECH_SECTOR_COMPANIES',
    'TECH_TICKER_LIST',
    'MACRO_CONTEXT_TERMS',
    'FINANCIAL_DATA_SOURCES'
]
