"""
SEC EDGAR Integration Utility

This module fetches real financial filing data from the SEC EDGAR database,
providing Python-verified fundamental data to combat hallucination.

Free, no API key needed - just requires proper User-Agent header.

Key Features:
- Company CIK lookup (ticker → CIK mapping)
- Fetch 10-K and 10-Q filings
- Extract filing metadata and URLs
- Parse key financial data from submissions

Usage:
    from utils.sec_edgar import get_company_filings, get_latest_10k, get_latest_10q
    
    filings = get_company_filings("AAPL", filing_type="10-K", count=5)
    latest_10k = get_latest_10k("MSFT")
"""

import re
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger
from utils.retry_helper import with_graceful_retry, SEARCH_API_RETRY_CONFIG


# SEC EDGAR requires a User-Agent header with contact information
# Format: "Company Name Contact@email.com"
SEC_USER_AGENT = "BettaFish-Investment-Research opensource@bettafish.ai"

# Base URLs for SEC EDGAR API
SEC_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# Common ticker → CIK mapping for major US tech stocks
# CIK numbers are zero-padded to 10 digits in the SEC system
TICKER_TO_CIK = {
    # Major Tech
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    
    # Semiconductors
    "AMD": "0000002488",
    "INTC": "0000050863",
    "QCOM": "0000804328",
    "AVGO": "0001730168",
    "TSM": "0001046179",
    "MU": "0000723125",
    "WDC": "0000106040",
    
    # Cloud & Enterprise
    "CRM": "0001108524",
    "ORCL": "0001341439",
    "IBM": "0000051143",
    "CSCO": "0000858877",
    "ADBE": "0000796343",
    "NOW": "0001373715",
    "SNOW": "0001640147",
    "PLTR": "0001321655",
    
    # AI & Growth
    "CRWD": "0001535527",
    "DDOG": "0001561550",
    "MDB": "0001441816",
}


def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Convert stock ticker to CIK (Central Index Key) number.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        
    Returns:
        CIK string (zero-padded to 10 digits) or None if not found
        
    Example:
        >>> get_cik_from_ticker("AAPL")
        '0000320193'
    """
    if not ticker:
        return None
    
    ticker = ticker.upper().strip()
    cik = TICKER_TO_CIK.get(ticker)
    
    if cik:
        logger.debug(f"Found CIK for {ticker}: {cik}")
        return cik
    else:
        logger.warning(f"CIK not found for ticker: {ticker}")
        return None


@with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=None)
def get_company_submissions(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch company filing submissions from SEC EDGAR.
    
    This returns ALL filings metadata for a company, which can then
    be filtered by filing type (10-K, 10-Q, 8-K, etc.)
    
    Args:
        ticker: Stock ticker symbol (e.g., "MSFT")
        
    Returns:
        Dictionary containing company info and recent filings, or None on error
        
    Example:
        >>> data = get_company_submissions("MSFT")
        >>> print(data['name'])
        'MICROSOFT CORP'
        >>> print(data['filings']['recent']['form'][:5])
        ['8-K', '10-Q', '10-K', '4', '8-K']
    """
    cik = get_cik_from_ticker(ticker)
    if not cik:
        logger.error(f"Cannot fetch submissions: No CIK found for {ticker}")
        return None
    
    url = SEC_SUBMISSIONS_URL.format(cik=cik)
    headers = {"User-Agent": SEC_USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"✅ Fetched SEC submissions for {ticker} (CIK: {cik})")
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"CIK {cik} not found in SEC database")
        else:
            logger.error(f"HTTP error fetching SEC data for {ticker}: {e}")
        return None
        
    except Exception as e:
        logger.exception(f"Error fetching SEC submissions for {ticker}: {e}")
        return None


def get_company_filings(
    ticker: str,
    filing_type: Optional[str] = None,
    count: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get filtered list of company filings from SEC EDGAR.
    
    Args:
        ticker: Stock ticker symbol
        filing_type: Filter by form type (e.g., "10-K", "10-Q", "8-K"). None = all types
        count: Maximum number of filings to return
        start_date: Filter filings after this date (YYYY-MM-DD format)
        end_date: Filter filings before this date (YYYY-MM-DD format)
        
    Returns:
        List of filing dictionaries containing:
        - form: Filing form type (e.g., "10-K")
        - filingDate: Date filed (YYYY-MM-DD)
        - reportDate: Period covered by the report (YYYY-MM-DD)
        - accessionNumber: SEC accession number
        - primaryDocument: Primary document filename
        - url: Direct URL to the filing
        
    Example:
        >>> filings = get_company_filings("AAPL", filing_type="10-K", count=3)
        >>> for f in filings:
        ...     print(f"{f['form']} filed {f['filingDate']}: {f['url']}")
    """
    submissions = get_company_submissions(ticker)
    if not submissions:
        return []
    
    try:
        recent = submissions.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        filing_dates = recent.get('filingDate', [])
        report_dates = recent.get('reportDate', [])
        accession_numbers = recent.get('accessionNumber', [])
        primary_documents = recent.get('primaryDocument', [])
        
        cik = get_cik_from_ticker(ticker)
        
        filings = []
        for i in range(len(forms)):
            # Apply filters
            if filing_type and forms[i] != filing_type:
                continue
            
            filing_date = filing_dates[i]
            
            if start_date and filing_date < start_date:
                continue
            if end_date and filing_date > end_date:
                continue
            
            # Build filing URL
            accession = accession_numbers[i].replace('-', '')
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{primary_documents[i]}"
            
            filing = {
                'form': forms[i],
                'filingDate': filing_date,
                'reportDate': report_dates[i] if i < len(report_dates) else None,
                'accessionNumber': accession_numbers[i],
                'primaryDocument': primary_documents[i],
                'url': doc_url
            }
            filings.append(filing)
            
            if len(filings) >= count:
                break
        
        logger.info(f"📄 Found {len(filings)} {filing_type or 'all'} filings for {ticker}")
        return filings
        
    except Exception as e:
        logger.exception(f"Error parsing filings for {ticker}: {e}")
        return []


def get_latest_10k(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent 10-K annual report filing.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Filing dictionary or None if not found
        
    Example:
        >>> filing = get_latest_10k("NVDA")
        >>> print(f"Latest 10-K filed on {filing['filingDate']}")
        >>> print(f"Download: {filing['url']}")
    """
    filings = get_company_filings(ticker, filing_type="10-K", count=1)
    if filings:
        logger.info(f"📊 Latest 10-K for {ticker}: filed {filings[0]['filingDate']}")
        return filings[0]
    else:
        logger.warning(f"No 10-K found for {ticker}")
        return None


def get_latest_10q(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent 10-Q quarterly report filing.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Filing dictionary or None if not found
        
    Example:
        >>> filing = get_latest_10q("MSFT")
        >>> print(f"Latest 10-Q filed on {filing['filingDate']}")
    """
    filings = get_company_filings(ticker, filing_type="10-Q", count=1)
    if filings:
        logger.info(f"📊 Latest 10-Q for {ticker}: filed {filings[0]['filingDate']}")
        return filings[0]
    else:
        logger.warning(f"No 10-Q found for {ticker}")
        return None


def get_recent_8k_filings(ticker: str, days: int = 30, count: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent 8-K current event reports.
    
    8-K filings are used to announce major corporate events like earnings,
    acquisitions, CEO changes, etc.
    
    Args:
        ticker: Stock ticker symbol
        days: Look back this many days
        count: Maximum number of filings to return
        
    Returns:
        List of 8-K filing dictionaries
        
    Example:
        >>> filings = get_recent_8k_filings("TSLA", days=90)
        >>> for f in filings:
        ...     print(f"{f['filingDate']}: {f['url']}")
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filings = get_company_filings(
        ticker,
        filing_type="8-K",
        count=count,
        start_date=start_date
    )
    
    if filings:
        logger.info(f"📰 Found {len(filings)} 8-K filings for {ticker} in last {days} days")
    
    return filings


def format_filings_for_prompt(filings: List[Dict[str, Any]], max_items: int = 5) -> str:
    """
    Format filing data for injection into LLM prompts.
    
    Args:
        filings: List of filing dictionaries
        max_items: Maximum number of filings to include
        
    Returns:
        Formatted string for prompt injection
    """
    if not filings:
        return "No SEC filings found."
    
    lines = ["**SEC EDGAR VERIFIED FILINGS:**"]
    for filing in filings[:max_items]:
        form = filing.get('form', 'Unknown')
        filed = filing.get('filingDate', 'N/A')
        report = filing.get('reportDate', 'N/A')
        url = filing.get('url', '')
        
        lines.append(f"- **{form}** (Filed: {filed}, Period: {report})")
        lines.append(f"  URL: {url}")
    
    if len(filings) > max_items:
        lines.append(f"\n(+{len(filings) - max_items} more filings available)")
    
    return "\n".join(lines)


def get_filing_summary(ticker: str) -> str:
    """
    Get a comprehensive summary of recent SEC filings for a company.
    
    This is a convenience function that fetches the most important filings
    (latest 10-K, 10-Q, and recent 8-Ks) and formats them for LLM consumption.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Formatted summary string
        
    Example:
        >>> summary = get_filing_summary("AAPL")
        >>> print(summary)
    """
    sections = []
    
    # Get latest 10-K (annual report)
    latest_10k = get_latest_10k(ticker)
    if latest_10k:
        sections.append("**Latest Annual Report (10-K):**")
        sections.append(f"Filed: {latest_10k['filingDate']} | Period: {latest_10k['reportDate']}")
        sections.append(f"URL: {latest_10k['url']}\n")
    
    # Get latest 10-Q (quarterly report)
    latest_10q = get_latest_10q(ticker)
    if latest_10q:
        sections.append("**Latest Quarterly Report (10-Q):**")
        sections.append(f"Filed: {latest_10q['filingDate']} | Period: {latest_10q['reportDate']}")
        sections.append(f"URL: {latest_10q['url']}\n")
    
    # Get recent 8-Ks (material events)
    recent_8ks = get_recent_8k_filings(ticker, days=90, count=5)
    if recent_8ks:
        sections.append(f"**Recent Material Events (8-K filings, last 90 days):**")
        for filing in recent_8ks:
            sections.append(f"- {filing['filingDate']}: {filing['url']}")
    
    if not sections:
        return f"⚠️ No SEC filings found for {ticker}"
    
    header = f"**SEC EDGAR FILING SUMMARY for {ticker}**\n"
    return header + "\n".join(sections)


# For testing/debugging
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = "NVDA"
    
    print(f"=== SEC EDGAR Test for {ticker} ===\n")
    
    # Test CIK lookup
    cik = get_cik_from_ticker(ticker)
    print(f"CIK: {cik}\n")
    
    # Test filing summary
    summary = get_filing_summary(ticker)
    print(summary)
    
    print("\n=== Recent 10-K Filings ===")
    filings_10k = get_company_filings(ticker, filing_type="10-K", count=3)
    for f in filings_10k:
        print(f"{f['form']} filed {f['filingDate']} (period: {f['reportDate']})")
        print(f"  → {f['url']}\n")
