"""
Insider Trading Data Parser
Uses SEC EDGAR's Form 4 filings to track insider trading activity.
This is FREE data from SEC - no API key needed.

Form 4: Insider Trading Disclosure (Buy/Sell by officers, directors, major shareholders)
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import re


@dataclass
class InsiderTransaction:
    """Represents a single insider trading transaction"""
    insider_name: str
    title: str  # e.g., CEO, Director, 10% Owner
    transaction_type: str  # Buy or Sell
    shares: float
    price_per_share: Optional[float]
    transaction_date: str
    filing_date: str
    value: Optional[float]  # Total transaction value


class InsiderTradingParser:
    """
    Parses SEC EDGAR Form 4 filings to extract insider trading data.
    """
    
    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        'User-Agent': 'BettaFish Research System research@bettafish.ai',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Convert ticker symbol to CIK (Central Index Key) using SEC's company tickers JSON.
        SEC provides this mapping for free.
        """
        try:
            # SEC provides a JSON mapping of all tickers to CIKs
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            companies = response.json()
            ticker_upper = ticker.upper()
            
            for company in companies.values():
                if company['ticker'] == ticker_upper:
                    # CIK needs to be padded to 10 digits with leading zeros
                    return str(company['cik_str']).zfill(10)
            
            return None
        except Exception as e:
            print(f"Error converting ticker to CIK: {e}")
            return None
    
    def get_insider_transactions(
        self, 
        ticker: str, 
        max_filings: int = 40
    ) -> List[InsiderTransaction]:
        """
        Fetch insider trading transactions for a given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            max_filings: Maximum number of Form 4 filings to retrieve
        
        Returns:
            List of InsiderTransaction objects
        """
        cik = self.get_cik_from_ticker(ticker)
        if not cik:
            print(f"Could not find CIK for ticker: {ticker}")
            return []
        
        # Get list of Form 4 filings
        filings_url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': '4',
            'dateb': '',
            'owner': 'include',
            'count': max_filings,
            'output': 'xml'
        }
        
        try:
            time.sleep(0.1)  # Be respectful to SEC servers
            response = self.session.get(filings_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse the XML response
            soup = BeautifulSoup(response.content, 'xml')
            filings = soup.find_all('filing')
            
            transactions = []
            for filing in filings[:max_filings]:
                filing_date = filing.find('filing-date')
                filing_href = filing.find('filing-href')
                
                if filing_date and filing_href:
                    # Parse individual Form 4
                    filing_transactions = self._parse_form4(
                        filing_href.text,
                        filing_date.text
                    )
                    transactions.extend(filing_transactions)
                    time.sleep(0.1)  # Rate limiting
            
            return transactions
        
        except Exception as e:
            print(f"Error fetching insider transactions: {e}")
            return []
    
    def _parse_form4(
        self, 
        filing_url: str, 
        filing_date: str
    ) -> List[InsiderTransaction]:
        """
        Parse a single Form 4 filing to extract transaction details.
        """
        transactions = []
        
        try:
            # Get the actual Form 4 XML
            response = self.session.get(filing_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            
            # Extract insider information
            reporting_owner = soup.find('reportingOwner')
            if not reporting_owner:
                return transactions
            
            insider_name = self._get_text(reporting_owner, 'rptOwnerName')
            title = self._get_text(reporting_owner, 'officerTitle')
            if not title:
                # Check if they're a director or 10% owner
                is_director = reporting_owner.find('isDirector')
                is_ten_percent = reporting_owner.find('isTenPercentOwner')
                if is_director and is_director.text == '1':
                    title = "Director"
                elif is_ten_percent and is_ten_percent.text == '1':
                    title = "10% Owner"
                else:
                    title = "Unknown"
            
            # Extract transactions (non-derivative)
            non_derivative_txs = soup.find_all('nonDerivativeTransaction')
            
            for tx in non_derivative_txs:
                tx_date = self._get_text(tx, 'transactionDate')
                tx_code = self._get_text(tx, 'transactionCode')
                
                # A = Award, P = Purchase, S = Sale
                if tx_code == 'P':
                    tx_type = 'Buy'
                elif tx_code == 'S':
                    tx_type = 'Sell'
                elif tx_code == 'A':
                    tx_type = 'Award'  # Stock grants/options
                else:
                    tx_type = tx_code
                
                shares_tag = tx.find('transactionShares')
                shares = float(shares_tag.find('value').text) if shares_tag else 0.0
                
                price_tag = tx.find('transactionPricePerShare')
                price = None
                if price_tag and price_tag.find('value'):
                    try:
                        price = float(price_tag.find('value').text)
                    except:
                        pass
                
                value = (shares * price) if (price and shares) else None
                
                transaction = InsiderTransaction(
                    insider_name=insider_name,
                    title=title,
                    transaction_type=tx_type,
                    shares=shares,
                    price_per_share=price,
                    transaction_date=tx_date,
                    filing_date=filing_date,
                    value=value
                )
                transactions.append(transaction)
        
        except Exception as e:
            print(f"Error parsing Form 4: {e}")
        
        return transactions
    
    def _get_text(self, parent, tag_name: str) -> str:
        """Helper to safely extract text from XML tag"""
        tag = parent.find(tag_name)
        if tag:
            value_tag = tag.find('value')
            if value_tag:
                return value_tag.text.strip()
            return tag.text.strip()
        return ""
    
    def get_summary(
        self, 
        ticker: str, 
        days: int = 90
    ) -> Dict[str, any]:
        """
        Generate a summary of insider trading activity over the specified period.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back (default 90)
        
        Returns:
            Dictionary with summary statistics:
            - net_shares: Net shares bought/sold
            - total_buys: Number of buy transactions
            - total_sells: Number of sell transactions
            - total_buy_value: Total $ value of buys
            - total_sell_value: Total $ value of sells
            - insiders_buying: List of insiders who bought
            - insiders_selling: List of insiders who sold
            - recent_transactions: Most recent transactions
        """
        transactions = self.get_insider_transactions(ticker)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_txs = [
            tx for tx in transactions
            if datetime.strptime(tx.transaction_date, '%Y-%m-%d') >= cutoff_date
        ]
        
        # Exclude awards/grants (not actual buy/sell)
        market_txs = [tx for tx in recent_txs if tx.transaction_type in ['Buy', 'Sell']]
        
        buy_txs = [tx for tx in market_txs if tx.transaction_type == 'Buy']
        sell_txs = [tx for tx in market_txs if tx.transaction_type == 'Sell']
        
        net_shares = (
            sum(tx.shares for tx in buy_txs) - 
            sum(tx.shares for tx in sell_txs)
        )
        
        total_buy_value = sum(
            tx.value for tx in buy_txs if tx.value is not None
        )
        total_sell_value = sum(
            tx.value for tx in sell_txs if tx.value is not None
        )
        
        insiders_buying = list(set(
            f"{tx.insider_name} ({tx.title})" for tx in buy_txs
        ))
        insiders_selling = list(set(
            f"{tx.insider_name} ({tx.title})" for tx in sell_txs
        ))
        
        return {
            'ticker': ticker,
            'period_days': days,
            'net_shares': net_shares,
            'total_buys': len(buy_txs),
            'total_sells': len(sell_txs),
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value,
            'net_value': total_buy_value - total_sell_value,
            'insiders_buying': insiders_buying,
            'insiders_selling': insiders_selling,
            'recent_transactions': market_txs[:10],  # Most recent 10
            'signal': self._interpret_signal(net_shares, total_buy_value, total_sell_value)
        }
    
    def _interpret_signal(
        self, 
        net_shares: float, 
        buy_value: float, 
        sell_value: float
    ) -> str:
        """
        Provide a simple interpretation of the insider trading signal.
        """
        if net_shares > 0 and buy_value > sell_value * 2:
            return "🟢 Strong Insider Buying Signal"
        elif net_shares > 0:
            return "🟡 Moderate Insider Buying"
        elif net_shares < 0 and sell_value > buy_value * 2:
            return "🔴 Strong Insider Selling Signal"
        elif net_shares < 0:
            return "🟠 Moderate Insider Selling"
        else:
            return "⚪ Neutral/No Significant Activity"


def print_insider_summary(summary: Dict):
    """Pretty print insider trading summary"""
    print(f"\n{'='*60}")
    print(f"Insider Trading Summary: {summary['ticker']}")
    print(f"Period: Last {summary['period_days']} days")
    print(f"{'='*60}")
    print(f"\n{summary['signal']}\n")
    print(f"Net Shares: {summary['net_shares']:,.0f}")
    print(f"Buy Transactions: {summary['total_buys']}")
    print(f"Sell Transactions: {summary['total_sells']}")
    print(f"Total Buy Value: ${summary['total_buy_value']:,.2f}")
    print(f"Total Sell Value: ${summary['total_sell_value']:,.2f}")
    print(f"Net Value: ${summary['net_value']:,.2f}")
    
    if summary['insiders_buying']:
        print(f"\n🟢 Insiders Buying:")
        for insider in summary['insiders_buying']:
            print(f"  - {insider}")
    
    if summary['insiders_selling']:
        print(f"\n🔴 Insiders Selling:")
        for insider in summary['insiders_selling']:
            print(f"  - {insider}")
    
    if summary['recent_transactions']:
        print(f"\n📊 Recent Transactions:")
        for tx in summary['recent_transactions'][:5]:
            value_str = f"${tx.value:,.0f}" if tx.value else "N/A"
            print(f"  {tx.transaction_date} | {tx.transaction_type:4s} | "
                  f"{tx.shares:8,.0f} shares @ ${tx.price_per_share:.2f} | "
                  f"{value_str:>15s} | {tx.insider_name} ({tx.title})")
    print(f"{'='*60}\n")


# Example usage
if __name__ == "__main__":
    parser = InsiderTradingParser()
    
    # Test with NVIDIA
    print("Fetching insider trading data for NVDA...")
    summary = parser.get_summary("NVDA", days=90)
    print_insider_summary(summary)
