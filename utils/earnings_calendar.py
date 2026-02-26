"""
Earnings Calendar Utility
Fetches upcoming earnings dates and analyst estimates.
Uses yfinance (FREE) as primary source.

Provides:
- Next earnings date
- Estimated EPS
- Number of analyst estimates
- Historical earnings surprise data
"""

import yfinance as yf
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd


@dataclass
class EarningsEvent:
    """Represents an earnings event"""
    ticker: str
    earnings_date: str
    estimated_eps: Optional[float] = None
    num_analysts: Optional[int] = None
    eps_surprise_percent: Optional[float] = None  # Historical average


@dataclass
class EarningsHistory:
    """Historical earnings data"""
    date: str
    reported_eps: float
    estimated_eps: float
    surprise: float
    surprise_percent: float


class EarningsCalendar:
    """
    Fetches earnings calendar data using yfinance.
    """
    
    def __init__(self):
        self.cache = {}
    
    def get_next_earnings(self, ticker: str) -> Optional[EarningsEvent]:
        """
        Get next earnings date and estimates for a ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            EarningsEvent object or None if not available
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get earnings calendar
            calendar = stock.calendar
            
            # Handle both Series and dict return types from yfinance
            if calendar is None:
                print(f"No earnings calendar data available for {ticker}")
                return None
            
            # Convert to dict if it's a Series
            if hasattr(calendar, 'to_dict'):
                calendar_dict = calendar.to_dict()
            elif isinstance(calendar, dict):
                calendar_dict = calendar
            else:
                print(f"Unexpected calendar format for {ticker}")
                return None
            
            if not calendar_dict:
                print(f"No earnings calendar data available for {ticker}")
                return None
            
            # Extract earnings date
            earnings_date = None
            if 'Earnings Date' in calendar_dict:
                earnings_date_val = calendar_dict['Earnings Date']
                
                # yfinance can return a range [start, end]
                if isinstance(earnings_date_val, pd.Timestamp):
                    earnings_date = earnings_date_val.strftime('%Y-%m-%d')
                elif isinstance(earnings_date_val, (list, tuple)) and len(earnings_date_val) > 0:
                    # Take the first date from range
                    first_date = earnings_date_val[0]
                    if isinstance(first_date, pd.Timestamp):
                        earnings_date = first_date.strftime('%Y-%m-%d')
                    else:
                        earnings_date = str(first_date)
                elif hasattr(earnings_date_val, '__iter__'):
                    # Pandas Series or similar
                    first_date = earnings_date_val.iloc[0] if hasattr(earnings_date_val, 'iloc') else list(earnings_date_val)[0]
                    if isinstance(first_date, pd.Timestamp):
                        earnings_date = first_date.strftime('%Y-%m-%d')
                    else:
                        earnings_date = str(first_date)
            
            # Extract EPS estimate
            estimated_eps = None
            num_analysts = None
            
            if 'Earnings Average' in calendar_dict:
                try:
                    estimated_eps = float(calendar_dict['Earnings Average'])
                except:
                    pass
            
            if 'Earnings Low' in calendar_dict and 'Earnings High' in calendar_dict:
                try:
                    # If we have range, use number of analysts as proxy for confidence
                    # yfinance doesn't always provide analyst count directly
                    low = float(calendar_dict['Earnings Low'])
                    high = float(calendar_dict['Earnings High'])
                    if estimated_eps is None and low and high:
                        estimated_eps = (low + high) / 2
                except:
                    pass
            
            # Get historical earnings surprise data
            avg_surprise = self._get_average_surprise(stock)
            
            if earnings_date:
                return EarningsEvent(
                    ticker=ticker.upper(),
                    earnings_date=earnings_date,
                    estimated_eps=estimated_eps,
                    num_analysts=num_analysts,
                    eps_surprise_percent=avg_surprise
                )
            
            return None
        
        except Exception as e:
            print(f"Error fetching earnings calendar for {ticker}: {e}")
            return None
    
    def _get_average_surprise(self, stock) -> Optional[float]:
        """
        Calculate average earnings surprise from historical data.
        """
        try:
            # Get earnings history
            earnings = stock.earnings_dates
            
            if earnings is None or earnings.empty:
                return None
            
            # Filter for reported earnings (not estimates for future)
            reported = earnings[earnings['Reported EPS'].notna()]
            
            if reported.empty:
                return None
            
            # Calculate surprise percentage
            surprises = []
            for idx, row in reported.head(8).iterrows():  # Last 8 quarters
                reported_eps = row['Reported EPS']
                estimated_eps = row.get('EPS Estimate', None)
                
                if pd.notna(reported_eps) and pd.notna(estimated_eps) and estimated_eps != 0:
                    surprise_pct = (reported_eps - estimated_eps) / abs(estimated_eps) * 100
                    surprises.append(surprise_pct)
            
            if surprises:
                return sum(surprises) / len(surprises)
            
            return None
        
        except Exception as e:
            return None
    
    def get_earnings_history(
        self, 
        ticker: str, 
        num_quarters: int = 8
    ) -> List[EarningsHistory]:
        """
        Get historical earnings data with surprise analysis.
        
        Args:
            ticker: Stock ticker symbol
            num_quarters: Number of past quarters to retrieve
        
        Returns:
            List of EarningsHistory objects
        """
        try:
            stock = yf.Ticker(ticker)
            earnings = stock.earnings_dates
            
            if earnings is None or earnings.empty:
                return []
            
            # Filter for reported earnings
            reported = earnings[earnings['Reported EPS'].notna()].head(num_quarters)
            
            history = []
            for idx, row in reported.iterrows():
                date = idx.strftime('%Y-%m-%d')
                reported_eps = row['Reported EPS']
                estimated_eps = row.get('EPS Estimate', None)
                
                surprise = None
                surprise_pct = None
                
                if pd.notna(estimated_eps) and estimated_eps != 0:
                    surprise = reported_eps - estimated_eps
                    surprise_pct = surprise / abs(estimated_eps) * 100
                
                history.append(EarningsHistory(
                    date=date,
                    reported_eps=float(reported_eps) if pd.notna(reported_eps) else 0.0,
                    estimated_eps=float(estimated_eps) if pd.notna(estimated_eps) else 0.0,
                    surprise=float(surprise) if surprise is not None else 0.0,
                    surprise_percent=float(surprise_pct) if surprise_pct is not None else 0.0
                ))
            
            return history
        
        except Exception as e:
            print(f"Error fetching earnings history for {ticker}: {e}")
            return []
    
    def get_earnings_catalyst_summary(self, ticker: str) -> Dict:
        """
        Generate comprehensive earnings catalyst summary.
        
        Returns:
            Dictionary with:
            - next_earnings_event
            - days_until_earnings
            - historical_surprise_pattern
            - earnings_history
            - catalyst_significance (score 0-100)
        """
        next_earnings = self.get_next_earnings(ticker)
        history = self.get_earnings_history(ticker)
        
        if not next_earnings:
            return {
                'ticker': ticker,
                'error': 'No upcoming earnings data available'
            }
        
        # Calculate days until earnings
        try:
            earnings_dt = datetime.strptime(next_earnings.earnings_date, '%Y-%m-%d')
            days_until = (earnings_dt - datetime.now()).days
        except:
            days_until = None
        
        # Analyze historical surprise pattern
        surprise_pattern = self._analyze_surprise_pattern(history)
        
        # Calculate catalyst significance score
        significance_score = self._calculate_catalyst_significance(
            next_earnings,
            history,
            days_until
        )
        
        return {
            'ticker': ticker,
            'next_earnings_event': next_earnings,
            'days_until_earnings': days_until,
            'historical_surprise_pattern': surprise_pattern,
            'earnings_history': history[:4],  # Last 4 quarters
            'catalyst_significance': significance_score,
            'interpretation': self._interpret_catalyst(significance_score, days_until)
        }
    
    def _analyze_surprise_pattern(self, history: List[EarningsHistory]) -> Dict:
        """Analyze patterns in earnings surprises"""
        if not history:
            return {'pattern': 'No Data'}
        
        recent = history[:4]  # Last 4 quarters
        
        beats = sum(1 for h in recent if h.surprise_percent > 0)
        misses = sum(1 for h in recent if h.surprise_percent < 0)
        
        avg_surprise = sum(h.surprise_percent for h in recent) / len(recent) if recent else 0
        
        if beats >= 3:
            pattern = "Consistent Beat"
        elif misses >= 3:
            pattern = "Concerning Misses"
        elif avg_surprise > 5:
            pattern = "Positive Trend"
        elif avg_surprise < -5:
            pattern = "Negative Trend"
        else:
            pattern = "Mixed/Neutral"
        
        return {
            'pattern': pattern,
            'beats': beats,
            'misses': misses,
            'avg_surprise_percent': avg_surprise,
            'last_4_quarters': [
                {
                    'date': h.date,
                    'surprise_percent': h.surprise_percent
                }
                for h in recent
            ]
        }
    
    def _calculate_catalyst_significance(
        self,
        next_earnings: EarningsEvent,
        history: List[EarningsHistory],
        days_until: Optional[int]
    ) -> int:
        """
        Calculate how significant this earnings event is (0-100).
        Higher score = more important catalyst.
        """
        score = 50  # Base score
        
        # Proximity boost (earnings soon = more significant)
        if days_until is not None:
            if days_until <= 7:
                score += 20
            elif days_until <= 30:
                score += 10
        
        # Historical surprise pattern
        if history:
            recent = history[:4]
            avg_surprise = sum(h.surprise_percent for h in recent) / len(recent)
            
            if abs(avg_surprise) > 10:
                score += 15  # High surprise magnitude = important
            
            # Consistency
            beats = sum(1 for h in recent if h.surprise_percent > 0)
            if beats == 4 or beats == 0:
                score += 10  # Very consistent = important
        
        # Estimate availability
        if next_earnings.estimated_eps is not None:
            score += 5  # Having estimates = more analyst coverage = important
        
        return min(100, max(0, score))
    
    def _interpret_catalyst(
        self,
        significance: int,
        days_until: Optional[int]
    ) -> str:
        """Interpret the catalyst significance"""
        urgency = ""
        if days_until is not None:
            if days_until <= 7:
                urgency = " (IMMINENT)"
            elif days_until <= 30:
                urgency = " (Soon)"
        
        if significance >= 80:
            return f"🔴 Critical Catalyst{urgency}"
        elif significance >= 65:
            return f"🟠 High Significance{urgency}"
        elif significance >= 50:
            return f"🟡 Moderate Significance{urgency}"
        else:
            return f"🟢 Lower Significance{urgency}"


def print_earnings_summary(summary: Dict):
    """Pretty print earnings catalyst summary"""
    if 'error' in summary:
        print(f"Error: {summary['error']}")
        return
    
    event = summary['next_earnings_event']
    
    print(f"\n{'='*70}")
    print(f"Earnings Catalyst Summary: {summary['ticker']}")
    print(f"{'='*70}\n")
    
    print(f"{summary['interpretation']}\n")
    print(f"Catalyst Significance Score: {summary['catalyst_significance']}/100\n")
    
    print(f"📅 Next Earnings Date: {event.earnings_date}")
    if summary['days_until_earnings'] is not None:
        print(f"   Days Until Earnings: {summary['days_until_earnings']}")
    
    if event.estimated_eps is not None:
        print(f"📊 Estimated EPS: ${event.estimated_eps:.2f}")
    
    if event.eps_surprise_percent is not None:
        print(f"📈 Average Historical Surprise: {event.eps_surprise_percent:+.1f}%")
    
    pattern = summary['historical_surprise_pattern']
    print(f"\n🎯 Historical Pattern: {pattern['pattern']}")
    print(f"   Last 4 Quarters: {pattern['beats']} Beats, {pattern['misses']} Misses")
    print(f"   Avg Surprise: {pattern['avg_surprise_percent']:+.1f}%")
    
    if summary['earnings_history']:
        print(f"\n📜 Recent Earnings History:")
        print(f"{'Date':<12} {'Reported':>10} {'Estimated':>10} {'Surprise':>10}")
        print("-" * 70)
        for h in summary['earnings_history']:
            print(f"{h.date:<12} ${h.reported_eps:>9.2f} ${h.estimated_eps:>9.2f} "
                  f"{h.surprise_percent:>9.1f}%")
    
    print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    calendar = EarningsCalendar()
    
    print("Fetching earnings calendar data for NVDA...")
    summary = calendar.get_earnings_catalyst_summary("NVDA")
    print_earnings_summary(summary)
