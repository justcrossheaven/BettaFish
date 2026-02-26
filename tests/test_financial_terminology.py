"""
Tests for prompts/financial_terminology.py
Tests term lookups, category completeness, data structure integrity.
"""

import pytest
from prompts import financial_terminology


class TestFinancialSearchTerms:
    """Test FINANCIAL_SEARCH_TERMS dictionary."""
    
    def test_financial_search_terms_exists(self):
        """Should have FINANCIAL_SEARCH_TERMS defined."""
        assert hasattr(financial_terminology, 'FINANCIAL_SEARCH_TERMS')
        assert isinstance(financial_terminology.FINANCIAL_SEARCH_TERMS, dict)
    
    def test_has_sentiment_categories(self):
        """Should have bullish, bearish, neutral categories."""
        terms = financial_terminology.FINANCIAL_SEARCH_TERMS
        assert 'bullish' in terms
        assert 'bearish' in terms
        assert 'neutral' in terms
    
    def test_bullish_terms_list(self):
        """Should have list of bullish terms."""
        bullish = financial_terminology.FINANCIAL_SEARCH_TERMS['bullish']
        assert isinstance(bullish, list)
        assert len(bullish) > 0
        assert 'moon' in bullish or 'rocket' in bullish
    
    def test_bearish_terms_list(self):
        """Should have list of bearish terms."""
        bearish = financial_terminology.FINANCIAL_SEARCH_TERMS['bearish']
        assert isinstance(bearish, list)
        assert len(bearish) > 0
        assert 'puts' in bearish or 'short' in bearish
    
    def test_reddit_specific_terms(self):
        """Should have Reddit-specific terminology."""
        terms = financial_terminology.FINANCIAL_SEARCH_TERMS
        assert 'reddit_specific' in terms
        reddit_terms = terms['reddit_specific']
        assert 'DD' in reddit_terms  # Due Diligence
        assert 'YOLO' in reddit_terms
        assert 'diamond hands' in reddit_terms
    
    def test_twitter_specific_terms(self):
        """Should have Twitter-specific terminology."""
        terms = financial_terminology.FINANCIAL_SEARCH_TERMS
        assert 'twitter_specific' in terms
        twitter_terms = terms['twitter_specific']
        assert '$ticker' in twitter_terms
        assert 'fintwit' in twitter_terms
    
    def test_no_empty_categories(self):
        """No category should be empty."""
        terms = financial_terminology.FINANCIAL_SEARCH_TERMS
        for category, term_list in terms.items():
            assert isinstance(term_list, list)
            assert len(term_list) > 0, f"Category '{category}' is empty"


class TestKeyMetrics:
    """Test KEY_METRICS list."""
    
    def test_key_metrics_exists(self):
        """Should have KEY_METRICS defined."""
        assert hasattr(financial_terminology, 'KEY_METRICS')
        assert isinstance(financial_terminology.KEY_METRICS, list)
    
    def test_has_valuation_metrics(self):
        """Should include key valuation metrics."""
        metrics = financial_terminology.KEY_METRICS
        assert 'P/E ratio' in metrics
        assert 'PEG ratio' in metrics
        assert 'P/S ratio' in metrics
    
    def test_has_profitability_metrics(self):
        """Should include profitability metrics."""
        metrics = financial_terminology.KEY_METRICS
        assert 'EPS' in metrics
        assert 'Revenue' in metrics
        assert 'Gross margin' in metrics or 'Operating margin' in metrics
    
    def test_has_balance_sheet_metrics(self):
        """Should include balance sheet health metrics."""
        metrics = financial_terminology.KEY_METRICS
        # Check for at least one balance sheet metric
        balance_sheet_terms = ['Net Debt/EBITDA', 'Current Ratio', 'Quick Ratio']
        assert any(term in metrics for term in balance_sheet_terms)
    
    def test_has_growth_metrics(self):
        """Should include growth metrics."""
        metrics = financial_terminology.KEY_METRICS
        assert 'YoY growth' in metrics or 'QoQ growth' in metrics
    
    def test_has_technical_indicators(self):
        """Should include technical indicators."""
        metrics = financial_terminology.KEY_METRICS
        assert 'RSI' in metrics or 'MACD' in metrics
    
    def test_metrics_are_strings(self):
        """All metrics should be strings."""
        metrics = financial_terminology.KEY_METRICS
        for metric in metrics:
            assert isinstance(metric, str)
            assert len(metric) > 0


class TestAccountingRedFlags:
    """Test ACCOUNTING_RED_FLAGS list."""
    
    def test_accounting_red_flags_exists(self):
        """Should have ACCOUNTING_RED_FLAGS defined."""
        assert hasattr(financial_terminology, 'ACCOUNTING_RED_FLAGS')
        assert isinstance(financial_terminology.ACCOUNTING_RED_FLAGS, list)
    
    def test_has_red_flags(self):
        """Should contain important red flags."""
        flags = financial_terminology.ACCOUNTING_RED_FLAGS
        assert len(flags) > 0
        # Check for some critical red flags
        critical_flags = ['Insider selling', 'Auditor resignation', 'Restatement']
        found = sum(1 for flag in critical_flags if flag in flags)
        assert found >= 2, "Should have at least 2 critical red flags"
    
    def test_includes_forensic_signals(self):
        """Should include forensic accounting signals."""
        flags = financial_terminology.ACCOUNTING_RED_FLAGS
        # DSO = Days Sales Outstanding
        forensic_terms = ['DSO increase', 'Inventory turnover', 'Goodwill impairment']
        found = sum(1 for term in forensic_terms if term in flags)
        assert found >= 1


class TestTechSectorCompanies:
    """Test TECH_SECTOR_COMPANIES dictionary."""
    
    def test_tech_sector_companies_exists(self):
        """Should have TECH_SECTOR_COMPANIES defined."""
        assert hasattr(financial_terminology, 'TECH_SECTOR_COMPANIES')
        assert isinstance(financial_terminology.TECH_SECTOR_COMPANIES, dict)
    
    def test_has_major_tech_companies(self):
        """Should include major tech companies."""
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        major_tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'META']
        for ticker in major_tickers:
            assert ticker in companies, f"Missing major tech company: {ticker}"
    
    def test_company_structure(self):
        """Each company should have name, sector, sub_sector."""
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        for ticker, info in companies.items():
            assert isinstance(info, dict)
            assert 'name' in info
            assert 'sector' in info
            assert 'sub_sector' in info
            assert isinstance(info['name'], str)
            assert isinstance(info['sector'], str)
            assert isinstance(info['sub_sector'], str)
    
    def test_ticker_format(self):
        """Tickers should be uppercase strings."""
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        for ticker in companies.keys():
            assert isinstance(ticker, str)
            assert ticker.isupper()
            assert 1 <= len(ticker) <= 5
    
    def test_has_semiconductor_companies(self):
        """Should include semiconductor companies."""
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        semiconductor_tickers = ['NVDA', 'AMD', 'INTC', 'TSM']
        found = sum(1 for ticker in semiconductor_tickers if ticker in companies)
        assert found >= 3, "Should have at least 3 semiconductor companies"
    
    def test_has_ai_infrastructure(self):
        """Should include AI infrastructure companies."""
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        # Check for companies with AI/Cloud/Data Center focus
        ai_related = []
        for ticker, info in companies.items():
            if 'AI' in info['sub_sector'] or 'Cloud' in info['sub_sector']:
                ai_related.append(ticker)
        assert len(ai_related) >= 2


class TestTechTickerList:
    """Test TECH_TICKER_LIST."""
    
    def test_tech_ticker_list_exists(self):
        """Should have TECH_TICKER_LIST defined."""
        assert hasattr(financial_terminology, 'TECH_TICKER_LIST')
        assert isinstance(financial_terminology.TECH_TICKER_LIST, list)
    
    def test_ticker_list_matches_companies(self):
        """TECH_TICKER_LIST should match keys of TECH_SECTOR_COMPANIES."""
        ticker_list = financial_terminology.TECH_TICKER_LIST
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        
        # Should have same tickers
        assert set(ticker_list) == set(companies.keys())
    
    def test_no_duplicates(self):
        """Should not have duplicate tickers."""
        ticker_list = financial_terminology.TECH_TICKER_LIST
        assert len(ticker_list) == len(set(ticker_list))


class TestMacroContextTerms:
    """Test MACRO_CONTEXT_TERMS list."""
    
    def test_macro_context_terms_exists(self):
        """Should have MACRO_CONTEXT_TERMS defined."""
        assert hasattr(financial_terminology, 'MACRO_CONTEXT_TERMS')
        assert isinstance(financial_terminology.MACRO_CONTEXT_TERMS, list)
    
    def test_has_interest_rate_terms(self):
        """Should include interest rate related terms."""
        terms = financial_terminology.MACRO_CONTEXT_TERMS
        rate_terms = ['Treasury yield', 'Fed funds rate', 'Powell speech']
        found = sum(1 for term in terms if any(rt in term for rt in rate_terms))
        assert found >= 1
    
    def test_has_inflation_terms(self):
        """Should include inflation terms."""
        terms = financial_terminology.MACRO_CONTEXT_TERMS
        assert any('inflation' in term.lower() or 'CPI' in term for term in terms)
    
    def test_has_geopolitical_terms(self):
        """Should include geopolitical risk terms."""
        terms = financial_terminology.MACRO_CONTEXT_TERMS
        geopolitical_keywords = ['Geopolitical', 'Export controls', 'Taiwan', 'China']
        found = sum(1 for term in terms if any(kw in term for kw in geopolitical_keywords))
        assert found >= 1


class TestFinancialDataSources:
    """Test FINANCIAL_DATA_SOURCES dictionary."""
    
    def test_financial_data_sources_exists(self):
        """Should have FINANCIAL_DATA_SOURCES defined."""
        assert hasattr(financial_terminology, 'FINANCIAL_DATA_SOURCES')
        assert isinstance(financial_terminology.FINANCIAL_DATA_SOURCES, dict)
    
    def test_has_tier_categories(self):
        """Should have tiered source categories."""
        sources = financial_terminology.FINANCIAL_DATA_SOURCES
        assert 'tier_1_official' in sources
        assert 'tier_2_news' in sources
        assert 'tier_3_analysis' in sources
        assert 'tier_4_social_sentiment' in sources
    
    def test_tier_1_has_sec_filings(self):
        """Tier 1 should include SEC filings."""
        tier_1 = financial_terminology.FINANCIAL_DATA_SOURCES['tier_1_official']
        assert isinstance(tier_1, list)
        assert any('SEC' in source or 'EDGAR' in source for source in tier_1)
    
    def test_tier_4_has_social_media(self):
        """Tier 4 should include social media sources."""
        tier_4 = financial_terminology.FINANCIAL_DATA_SOURCES['tier_4_social_sentiment']
        assert isinstance(tier_4, list)
        social_platforms = ['Twitter', 'Reddit', 'StockTwits']
        found = sum(1 for source in tier_4 if any(platform in source for platform in social_platforms))
        assert found >= 2
    
    def test_all_tiers_non_empty(self):
        """All tiers should have sources listed."""
        sources = financial_terminology.FINANCIAL_DATA_SOURCES
        for tier_name, source_list in sources.items():
            assert isinstance(source_list, list)
            assert len(source_list) > 0, f"Tier '{tier_name}' is empty"


class TestDataStructureIntegrity:
    """Test overall data structure integrity."""
    
    def test_no_none_values(self):
        """Should not contain None values."""
        # Check all major data structures
        structures = [
            financial_terminology.FINANCIAL_SEARCH_TERMS,
            financial_terminology.KEY_METRICS,
            financial_terminology.ACCOUNTING_RED_FLAGS,
            financial_terminology.TECH_SECTOR_COMPANIES,
            financial_terminology.MACRO_CONTEXT_TERMS,
            financial_terminology.FINANCIAL_DATA_SOURCES
        ]
        
        for structure in structures:
            if isinstance(structure, dict):
                for key, value in structure.items():
                    assert value is not None
                    if isinstance(value, (list, dict)):
                        assert len(value) > 0
            elif isinstance(structure, list):
                for item in structure:
                    assert item is not None
    
    def test_consistent_naming_conventions(self):
        """Should use consistent naming for tickers."""
        # All ticker references should be uppercase
        companies = financial_terminology.TECH_SECTOR_COMPANIES
        ticker_list = financial_terminology.TECH_TICKER_LIST
        
        for ticker in companies.keys():
            assert ticker == ticker.upper()
        
        for ticker in ticker_list:
            assert ticker == ticker.upper()
    
    def test_module_completeness(self):
        """Should have all expected exports."""
        expected_attrs = [
            'FINANCIAL_SEARCH_TERMS',
            'KEY_METRICS',
            'ACCOUNTING_RED_FLAGS',
            'TECH_SECTOR_COMPANIES',
            'TECH_TICKER_LIST',
            'MACRO_CONTEXT_TERMS',
            'FINANCIAL_DATA_SOURCES'
        ]
        
        for attr in expected_attrs:
            assert hasattr(financial_terminology, attr), f"Missing expected attribute: {attr}"
