"""
Market Data Utility - Anti-Hallucination Module

This module provides Python-guaranteed real-time market data that serves as
immutable "truth anchors" for LLM-generated reports. By injecting verified
stock prices and dates at the Python layer, we prevent the LLM from
hallucinating future dates or incorrect stock prices.

Usage:
    from utils.market_data import get_market_snapshot, extract_ticker_from_query
    
    ticker = extract_ticker_from_query("Microsoft AI strategy analysis")
    if ticker:
        snapshot = get_market_snapshot(ticker)
        # snapshot = {'ticker': 'MSFT', 'current_price': 415.23, 'query_date': '2025-01-30', ...}
"""

from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger


# Common company name to ticker mapping for US tech stocks
TICKER_MAPPING = {
    # Major Tech
    "microsoft": "MSFT",
    "msft": "MSFT",
    "apple": "AAPL",
    "aapl": "AAPL",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "googl": "GOOGL",
    "goog": "GOOG",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "tesla": "TSLA",
    "tsla": "TSLA",
    
    # Semiconductors
    "amd": "AMD",
    "intel": "INTC",
    "intc": "INTC",
    "qualcomm": "QCOM",
    "qcom": "QCOM",
    "broadcom": "AVGO",
    "avgo": "AVGO",
    "tsmc": "TSM",
    "tsm": "TSM",
    "micron": "MU",
    "mu": "MU",
    "western digital": "WDC",
    "wdc": "WDC",
    
    # Cloud & Enterprise
    "salesforce": "CRM",
    "crm": "CRM",
    "oracle": "ORCL",
    "orcl": "ORCL",
    "ibm": "IBM",
    "cisco": "CSCO",
    "csco": "CSCO",
    "adobe": "ADBE",
    "adbe": "ADBE",
    "servicenow": "NOW",
    "now": "NOW",
    "snowflake": "SNOW",
    "snow": "SNOW",
    "palantir": "PLTR",
    "pltr": "PLTR",
    
    # AI & Growth
    "openai": None,  # Not publicly traded
    "anthropic": None,  # Not publicly traded
    "crowdstrike": "CRWD",
    "crwd": "CRWD",
    "datadog": "DDOG",
    "ddog": "DDOG",
    "mongodb": "MDB",
    "mdb": "MDB",
}


def extract_ticker_from_query(query: str) -> Optional[str]:
    """
    Extract ticker symbol from a natural language query.
    
    Uses a simple keyword→ticker mapping. For more sophisticated
    extraction, consider NLP-based entity recognition.
    
    Args:
        query: Natural language query (e.g., "Microsoft AI strategy analysis")
        
    Returns:
        Ticker symbol (e.g., "MSFT") or None if not found
        
    Example:
        >>> extract_ticker_from_query("Microsoft stock analysis")
        'MSFT'
        >>> extract_ticker_from_query("NVDA earnings report")
        'NVDA'
    """
    if not query:
        return None
    
    query_lower = query.lower()
    
    # First check for exact ticker matches (uppercase in original query)
    words = query.split()
    for word in words:
        # Check if word looks like a ticker (1-5 uppercase letters)
        clean_word = word.strip(",.;:!?()[]{}\"'").upper()
        if 1 <= len(clean_word) <= 5 and clean_word.isalpha():
            # Check if it's a known ticker
            if clean_word.lower() in TICKER_MAPPING:
                result = TICKER_MAPPING[clean_word.lower()]
                if result:
                    logger.debug(f"Extracted ticker '{result}' from query word '{word}'")
                    return result
    
    # Then check for company name matches
    for company, ticker in TICKER_MAPPING.items():
        if company in query_lower and ticker is not None:
            logger.debug(f"Extracted ticker '{ticker}' from company name '{company}'")
            return ticker
    
    logger.debug(f"No ticker found in query: {query[:50]}...")
    return None


def get_market_snapshot(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Python-guaranteed real-time market snapshot.
    
    This data serves as the "Source of Truth" for all LLM-generated reports,
    preventing hallucination of dates and stock prices.
    
    Args:
        ticker: Stock ticker symbol (e.g., "MSFT", "NVDA")
        
    Returns:
        Dictionary containing:
        - ticker: The ticker symbol
        - current_price: Latest stock price (float)
        - currency: Currency code (usually "USD")
        - query_date: Current date in YYYY-MM-DD format
        - query_time: Current time in HH:MM:SS format
        - status: "REAL_TIME_VERIFIED" or "FALLBACK"
        
        Returns None if fetching fails completely.
        
    Example:
        >>> snapshot = get_market_snapshot("MSFT")
        >>> print(snapshot)
        {'ticker': 'MSFT', 'current_price': 415.23, 'currency': 'USD', 
         'query_date': '2025-01-30', 'query_time': '14:30:00', 
         'status': 'REAL_TIME_VERIFIED'}
    """
    if not ticker:
        logger.warning("get_market_snapshot called with empty ticker")
        return None
    
    ticker = ticker.upper().strip()
    now = datetime.now()
    
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        
        # Try to get the most recent price
        current_price = None
        
        # Method 1: Try today's history
        try:
            todays_data = stock.history(period='1d')
            if not todays_data.empty:
                current_price = float(todays_data['Close'].iloc[-1])
        except Exception as e:
            logger.debug(f"Could not get today's history for {ticker}: {e}")
        
        # Method 2: Fallback to info dict
        if current_price is None:
            try:
                info = stock.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                if current_price:
                    current_price = float(current_price)
            except Exception as e:
                logger.debug(f"Could not get info for {ticker}: {e}")
        
        # Method 3: Try 5-day history
        if current_price is None:
            try:
                hist = stock.history(period='5d')
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            except Exception as e:
                logger.debug(f"Could not get 5-day history for {ticker}: {e}")
        
        if current_price is not None:
            snapshot = {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "currency": "USD",
                "query_date": now.strftime("%Y-%m-%d"),
                "query_time": now.strftime("%H:%M:%S"),
                "status": "REAL_TIME_VERIFIED"
            }
            logger.info(f"🔒 Market snapshot for {ticker}: ${snapshot['current_price']} @ {snapshot['query_date']}")
            return snapshot
        else:
            logger.warning(f"Could not fetch price for {ticker} - all methods failed")
            return _create_fallback_snapshot(ticker, now, "NO_PRICE_DATA")
            
    except ImportError:
        logger.error("yfinance not installed. Run: pip install yfinance")
        return _create_fallback_snapshot(ticker, now, "YFINANCE_NOT_INSTALLED")
        
    except Exception as e:
        logger.exception(f"Error fetching market data for {ticker}: {e}")
        return _create_fallback_snapshot(ticker, now, f"ERROR: {str(e)[:50]}")


def _create_fallback_snapshot(ticker: str, now: datetime, reason: str) -> Dict[str, Any]:
    """
    Create a fallback snapshot when real data is unavailable.
    
    The fallback still provides the correct date to prevent date hallucination,
    but marks price as unknown.
    """
    snapshot = {
        "ticker": ticker,
        "current_price": None,
        "currency": "USD",
        "query_date": now.strftime("%Y-%m-%d"),
        "query_time": now.strftime("%H:%M:%S"),
        "status": f"FALLBACK ({reason})"
    }
    logger.warning(f"⚠️ Using fallback snapshot for {ticker}: {reason}")
    return snapshot


def format_market_anchor_for_prompt(snapshot: Optional[Dict[str, Any]]) -> str:
    """
    Format market snapshot data for injection into LLM prompts.
    
    Args:
        snapshot: Market snapshot from get_market_snapshot()
        
    Returns:
        Formatted string for prompt injection
    """
    if not snapshot:
        return ""
    
    price_str = f"${snapshot['current_price']}" if snapshot.get('current_price') else "UNAVAILABLE"
    
    return f"""
**MARKET ANCHOR PROTOCOL (PYTHON-VERIFIED DATA)**
- Current Date: {snapshot['query_date']}
- Target Ticker: {snapshot['ticker']}
- Reference Price: {price_str}
- Data Status: {snapshot['status']}

**ANTI-HALLUCINATION RULES:**
1. DO NOT invent dates in the future. Today is {snapshot['query_date']}.
2. When discussing stock price, use {price_str} as the baseline.
3. If you see conflicting dates/prices in source data, trust THIS anchor.
"""


# For testing/debugging
if __name__ == "__main__":
    # Test ticker extraction
    test_queries = [
        "Microsoft AI strategy analysis",
        "NVDA earnings report Q4",
        "What is Apple's PE ratio?",
        "Tesla vs BYD comparison",
        "Unknown company analysis"
    ]
    
    print("=== Ticker Extraction Test ===")
    for q in test_queries:
        ticker = extract_ticker_from_query(q)
        print(f"Query: '{q}' -> Ticker: {ticker}")
    
    print("\n=== Market Snapshot Test ===")
    # Test market snapshot
    snapshot = get_market_snapshot("MSFT")
    if snapshot:
        print(f"Snapshot: {snapshot}")
        print(f"\nFormatted for prompt:\n{format_market_anchor_for_prompt(snapshot)}")
    else:
        print("Failed to get snapshot")
