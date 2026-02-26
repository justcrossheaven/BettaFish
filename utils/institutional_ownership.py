"""
Institutional Ownership Parser (13F Filings)
Tracks major institutional holders and their quarterly position changes.
Data source: SEC EDGAR 13F filings (FREE, no API key needed)

13F: Quarterly report of institutional investment managers with >$100M AUM
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
import re


@dataclass
class InstitutionalPosition:
    """Represents an institutional holder's position"""
    institution_name: str
    shares: int
    value: float  # In USD
    quarter: str  # Format: YYYY-QX
    filing_date: str
    percent_change: Optional[float] = None  # QoQ change


@dataclass
class PositionChange:
    """Represents a significant change in institutional position"""
    institution_name: str
    change_type: str  # 'NEW', 'EXIT', 'INCREASE', 'DECREASE'
    previous_shares: int
    current_shares: int
    change_percent: float
    current_value: float
    quarter: str


class InstitutionalOwnershipParser:
    """
    Parses SEC EDGAR 13F filings to track institutional ownership.
    """
    
    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        'User-Agent': 'BettaFish Research System research@bettafish.ai',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    # Major institutional investors CIKs (for quick analysis)
    MAJOR_INSTITUTIONS = {
        'Vanguard Group': '0000102909',
        'BlackRock': '0001086364',
        'State Street': '0000093751',
        'Fidelity': '0000315066',
        'Geode Capital': '0001214717',
        'Morgan Stanley': '0000895421',
        'Goldman Sachs': '0000886982',
        'JPMorgan Chase': '0000019617',
        'Bank of America': '0000070858',
        'Capital Research': '0000721371',
        'T. Rowe Price': '0000794254',
        'Wellington Management': '0000104659',
        'Invesco': '0000914208',
        'Northern Trust': '0000073124',
        'Charles Schwab': '0000316709',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Convert ticker to CIK using SEC's company tickers JSON"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            companies = response.json()
            ticker_upper = ticker.upper()
            
            for company in companies.values():
                if company['ticker'] == ticker_upper:
                    return str(company['cik_str']).zfill(10)
            
            return None
        except Exception as e:
            print(f"Error converting ticker to CIK: {e}")
            return None
    
    def get_major_holders(
        self, 
        ticker: str, 
        num_quarters: int = 2
    ) -> Dict[str, List[InstitutionalPosition]]:
        """
        Get positions from major institutional holders for the specified ticker.
        
        Args:
            ticker: Stock ticker symbol
            num_quarters: Number of recent quarters to fetch (default 2 for QoQ comparison)
        
        Returns:
            Dictionary mapping quarter -> list of positions
        """
        cik = self.get_cik_from_ticker(ticker)
        if not cik:
            print(f"Could not find CIK for ticker: {ticker}")
            return {}
        
        all_positions = {}
        
        for inst_name, inst_cik in self.MAJOR_INSTITUTIONS.items():
            print(f"Checking {inst_name}...")
            positions = self._get_institution_positions(inst_cik, cik, ticker, num_quarters)
            
            for position in positions:
                if position.quarter not in all_positions:
                    all_positions[position.quarter] = []
                all_positions[position.quarter].append(position)
            
            time.sleep(0.1)  # Rate limiting
        
        return all_positions
    
    def _get_institution_positions(
        self,
        institution_cik: str,
        target_cik: str,
        ticker: str,
        num_quarters: int
    ) -> List[InstitutionalPosition]:
        """
        Get specific institution's positions in a target company over time.
        """
        positions = []
        
        try:
            # Get list of 13F filings
            filings_url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': institution_cik,
                'type': '13F-HR',
                'dateb': '',
                'count': num_quarters,
                'output': 'xml'
            }
            
            response = self.session.get(filings_url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            filings = soup.find_all('filing')
            
            for filing in filings[:num_quarters]:
                filing_date = filing.find('filing-date')
                filing_href = filing.find('filing-href')
                
                if not (filing_date and filing_href):
                    continue
                
                # Extract quarter from filing date
                date = filing_date.text
                year = date[:4]
                month = int(date[5:7])
                quarter = f"{year}-Q{(month-1)//3 + 1}"
                
                # Parse the 13F to find holdings of target company
                position = self._parse_13f_for_ticker(
                    filing_href.text,
                    target_cik,
                    ticker,
                    quarter,
                    date
                )
                
                if position:
                    positions.append(position)
                
                time.sleep(0.1)
        
        except Exception as e:
            print(f"Error fetching institution positions: {e}")
        
        return positions
    
    def _parse_13f_for_ticker(
        self,
        filing_url: str,
        target_cik: str,
        ticker: str,
        quarter: str,
        filing_date: str
    ) -> Optional[InstitutionalPosition]:
        """
        Parse a 13F filing to find position in specific ticker.
        """
        try:
            # 13F filings have an information table (XML)
            # We need to find the "informationTable.xml" file
            response = self.session.get(filing_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the information table link
            table_link = None
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'informationTable.xml' in href or 'infotable.xml' in href.lower():
                    table_link = self.BASE_URL + href
                    break
            
            if not table_link:
                return None
            
            # Parse the information table
            time.sleep(0.1)
            table_response = self.session.get(table_link, timeout=15)
            table_response.raise_for_status()
            
            table_soup = BeautifulSoup(table_response.content, 'xml')
            
            # Find holdings matching our ticker
            info_tables = table_soup.find_all('infoTable')
            
            for table in info_tables:
                name_tag = table.find('nameOfIssuer')
                cusip_tag = table.find('cusip')
                
                if name_tag and ticker.upper() in name_tag.text.upper():
                    shares_tag = table.find('sshPrnamt')
                    value_tag = table.find('value')
                    
                    if shares_tag and value_tag:
                        # Get institution name from the filing
                        filer = table_soup.find('filingManager')
                        inst_name = "Unknown"
                        if filer:
                            name = filer.find('name')
                            if name:
                                inst_name = name.text.strip()
                        
                        shares = int(shares_tag.text)
                        value = float(value_tag.text) * 1000  # Value is in thousands
                        
                        return InstitutionalPosition(
                            institution_name=inst_name,
                            shares=shares,
                            value=value,
                            quarter=quarter,
                            filing_date=filing_date
                        )
        
        except Exception as e:
            print(f"Error parsing 13F: {e}")
        
        return None
    
    def analyze_position_changes(
        self,
        positions_by_quarter: Dict[str, List[InstitutionalPosition]],
        min_change_threshold: float = 0.20  # 20% change
    ) -> List[PositionChange]:
        """
        Analyze quarter-over-quarter position changes and flag significant moves.
        
        Args:
            positions_by_quarter: Output from get_major_holders()
            min_change_threshold: Minimum % change to flag (default 20%)
        
        Returns:
            List of significant position changes
        """
        if len(positions_by_quarter) < 2:
            return []
        
        # Sort quarters
        quarters = sorted(positions_by_quarter.keys(), reverse=True)
        current_quarter = quarters[0]
        previous_quarter = quarters[1]
        
        current_positions = {
            pos.institution_name: pos 
            for pos in positions_by_quarter[current_quarter]
        }
        previous_positions = {
            pos.institution_name: pos 
            for pos in positions_by_quarter[previous_quarter]
        }
        
        changes = []
        
        # Check for NEW positions
        for inst_name, current_pos in current_positions.items():
            if inst_name not in previous_positions:
                changes.append(PositionChange(
                    institution_name=inst_name,
                    change_type='NEW',
                    previous_shares=0,
                    current_shares=current_pos.shares,
                    change_percent=100.0,
                    current_value=current_pos.value,
                    quarter=current_quarter
                ))
        
        # Check for EXITS
        for inst_name, prev_pos in previous_positions.items():
            if inst_name not in current_positions:
                changes.append(PositionChange(
                    institution_name=inst_name,
                    change_type='EXIT',
                    previous_shares=prev_pos.shares,
                    current_shares=0,
                    change_percent=-100.0,
                    current_value=0,
                    quarter=current_quarter
                ))
        
        # Check for INCREASES/DECREASES
        for inst_name in current_positions:
            if inst_name in previous_positions:
                current_pos = current_positions[inst_name]
                prev_pos = previous_positions[inst_name]
                
                if prev_pos.shares == 0:
                    continue
                
                change_pct = (
                    (current_pos.shares - prev_pos.shares) / prev_pos.shares * 100
                )
                
                if abs(change_pct) >= min_change_threshold * 100:
                    change_type = 'INCREASE' if change_pct > 0 else 'DECREASE'
                    
                    changes.append(PositionChange(
                        institution_name=inst_name,
                        change_type=change_type,
                        previous_shares=prev_pos.shares,
                        current_shares=current_pos.shares,
                        change_percent=change_pct,
                        current_value=current_pos.value,
                        quarter=current_quarter
                    ))
        
        # Sort by absolute change percent
        changes.sort(key=lambda x: abs(x.change_percent), reverse=True)
        
        return changes
    
    def get_ownership_summary(
        self,
        ticker: str
    ) -> Dict:
        """
        Generate comprehensive institutional ownership summary.
        
        Returns:
            Dictionary with:
            - total_institutional_shares
            - top_holders
            - significant_changes
            - new_positions
            - exits
            - bullish_signal_score (0-100)
        """
        positions_by_quarter = self.get_major_holders(ticker, num_quarters=2)
        
        if not positions_by_quarter:
            return {
                'ticker': ticker,
                'error': 'No institutional data found'
            }
        
        quarters = sorted(positions_by_quarter.keys(), reverse=True)
        latest_quarter = quarters[0]
        latest_positions = positions_by_quarter[latest_quarter]
        
        # Calculate totals
        total_shares = sum(pos.shares for pos in latest_positions)
        total_value = sum(pos.value for pos in latest_positions)
        
        # Top holders
        top_holders = sorted(
            latest_positions, 
            key=lambda x: x.shares, 
            reverse=True
        )[:10]
        
        # Analyze changes
        changes = self.analyze_position_changes(positions_by_quarter)
        
        new_positions = [c for c in changes if c.change_type == 'NEW']
        exits = [c for c in changes if c.change_type == 'EXIT']
        increases = [c for c in changes if c.change_type == 'INCREASE']
        decreases = [c for c in changes if c.change_type == 'DECREASE']
        
        # Calculate bullish signal score
        # More buying/new positions = higher score
        bullish_score = min(100, max(0, (
            len(new_positions) * 15 + 
            len(increases) * 10 - 
            len(exits) * 15 - 
            len(decreases) * 10 + 
            50  # Base score
        )))
        
        return {
            'ticker': ticker,
            'latest_quarter': latest_quarter,
            'total_institutional_shares': total_shares,
            'total_institutional_value': total_value,
            'num_major_holders': len(latest_positions),
            'top_holders': top_holders,
            'significant_changes': changes,
            'new_positions': new_positions,
            'exits': exits,
            'increases': increases,
            'decreases': decreases,
            'bullish_signal_score': bullish_score,
            'signal_interpretation': self._interpret_signal(bullish_score)
        }
    
    def _interpret_signal(self, score: float) -> str:
        """Interpret the bullish signal score"""
        if score >= 70:
            return "🟢 Strong Institutional Accumulation"
        elif score >= 55:
            return "🟡 Moderate Institutional Buying"
        elif score >= 45:
            return "⚪ Neutral - Mixed Signals"
        elif score >= 30:
            return "🟠 Moderate Institutional Selling"
        else:
            return "🔴 Strong Institutional Distribution"


def print_ownership_summary(summary: Dict):
    """Pretty print institutional ownership summary"""
    if 'error' in summary:
        print(f"Error: {summary['error']}")
        return
    
    print(f"\n{'='*70}")
    print(f"Institutional Ownership Summary: {summary['ticker']}")
    print(f"Quarter: {summary['latest_quarter']}")
    print(f"{'='*70}")
    print(f"\n{summary['signal_interpretation']}")
    print(f"Bullish Score: {summary['bullish_signal_score']:.0f}/100\n")
    
    print(f"Total Institutional Shares: {summary['total_institutional_shares']:,}")
    print(f"Total Value: ${summary['total_institutional_value']:,.0f}")
    print(f"Number of Major Holders: {summary['num_major_holders']}\n")
    
    print("🏆 Top Institutional Holders:")
    for i, holder in enumerate(summary['top_holders'][:5], 1):
        print(f"  {i}. {holder.institution_name}")
        print(f"     Shares: {holder.shares:,} | Value: ${holder.value:,.0f}\n")
    
    if summary['new_positions']:
        print("🆕 New Positions (Quarter-over-Quarter):")
        for change in summary['new_positions'][:3]:
            print(f"  - {change.institution_name}: {change.current_shares:,} shares "
                  f"(${change.current_value:,.0f})")
    
    if summary['exits']:
        print("\n🚪 Exits (Quarter-over-Quarter):")
        for change in summary['exits'][:3]:
            print(f"  - {change.institution_name}: Exited {change.previous_shares:,} shares")
    
    if summary['increases']:
        print("\n📈 Significant Increases (>20%):")
        for change in summary['increases'][:3]:
            print(f"  - {change.institution_name}: +{change.change_percent:.1f}% "
                  f"({change.current_shares:,} shares)")
    
    if summary['decreases']:
        print("\n📉 Significant Decreases (>20%):")
        for change in summary['decreases'][:3]:
            print(f"  - {change.institution_name}: {change.change_percent:.1f}% "
                  f"({change.current_shares:,} shares)")
    
    print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    parser = InstitutionalOwnershipParser()
    
    print("Fetching institutional ownership data for NVDA...")
    summary = parser.get_ownership_summary("NVDA")
    print_ownership_summary(summary)
