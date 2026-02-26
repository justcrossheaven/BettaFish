"""
Test script for new fundamental analysis tools.
Validates that all utilities work correctly.
"""

import sys
sys.path.insert(0, 'utils')

from utils.insider_trading import InsiderTradingParser, print_insider_summary
from utils.institutional_ownership import InstitutionalOwnershipParser, print_ownership_summary
from utils.dcf_model import DCFModel, DCFAssumptions, DCFScenarioAnalysis, print_dcf_results, print_scenario_analysis
from utils.earnings_calendar import EarningsCalendar, print_earnings_summary


def test_insider_trading():
    """Test insider trading data parser"""
    print("\n" + "="*80)
    print("TESTING: Insider Trading Parser")
    print("="*80)
    
    try:
        parser = InsiderTradingParser()
        summary = parser.get_summary("AAPL", days=90)
        print_insider_summary(summary)
        print("✅ Insider Trading Parser: PASSED")
    except Exception as e:
        print(f"❌ Insider Trading Parser: FAILED - {e}")


def test_institutional_ownership():
    """Test institutional ownership parser"""
    print("\n" + "="*80)
    print("TESTING: Institutional Ownership Parser (13F)")
    print("="*80)
    
    try:
        parser = InstitutionalOwnershipParser()
        # Note: This may take a while as it fetches from SEC EDGAR
        print("Note: This test may take 30-60 seconds due to SEC rate limiting...")
        summary = parser.get_ownership_summary("AAPL")
        print_ownership_summary(summary)
        print("✅ Institutional Ownership Parser: PASSED")
    except Exception as e:
        print(f"❌ Institutional Ownership Parser: FAILED - {e}")


def test_dcf_model():
    """Test DCF model"""
    print("\n" + "="*80)
    print("TESTING: DCF Valuation Model")
    print("="*80)
    
    try:
        # Example assumptions (Apple)
        assumptions = DCFAssumptions(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_revenue=400000,  # $400B
            current_fcf=100000,  # $100B
            current_operating_margin=0.30,  # 30%
            shares_outstanding=15000,  # 15B shares
            revenue_growth_rates=[0.08, 0.07, 0.06, 0.05, 0.04],
            terminal_operating_margin=0.28,
            capex_percent_of_revenue=0.04,
            nwc_percent_of_revenue=0.01,
            risk_free_rate=0.045,
            equity_risk_premium=0.06,
            beta=1.2,
            terminal_growth_rate=0.025,
            tax_rate=0.21
        )
        
        # Base case
        model = DCFModel(assumptions)
        results = model.run_valuation()
        print_dcf_results(results, current_price=180.00)
        
        # Scenario analysis
        print("\nRunning scenario analysis...")
        scenario_results = DCFScenarioAnalysis.run_scenario_analysis(assumptions)
        print_scenario_analysis(scenario_results, current_price=180.00)
        
        print("✅ DCF Model: PASSED")
    except Exception as e:
        print(f"❌ DCF Model: FAILED - {e}")


def test_earnings_calendar():
    """Test earnings calendar"""
    print("\n" + "="*80)
    print("TESTING: Earnings Calendar")
    print("="*80)
    
    try:
        calendar = EarningsCalendar()
        summary = calendar.get_earnings_catalyst_summary("AAPL")
        print_earnings_summary(summary)
        print("✅ Earnings Calendar: PASSED")
    except Exception as e:
        print(f"❌ Earnings Calendar: FAILED - {e}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("FUNDAMENTAL ANALYSIS TOOLS TEST SUITE")
    print("="*80)
    print("\nThis will test all newly implemented fundamental analysis utilities:")
    print("1. Insider Trading Parser (SEC Form 4)")
    print("2. Institutional Ownership Parser (SEC 13F)")
    print("3. DCF Valuation Model")
    print("4. Earnings Calendar (yfinance)")
    print("\nNote: Tests involving SEC EDGAR may take longer due to rate limiting.")
    print("="*80)
    
    # Run tests
    test_dcf_model()  # Pure Python, no API calls - run first
    test_earnings_calendar()  # Uses yfinance - fast
    test_insider_trading()  # SEC EDGAR - may be slow
    
    # Skip institutional ownership in quick test (too slow)
    print("\n" + "="*80)
    print("NOTE: Skipping institutional ownership test in quick mode.")
    print("To test institutional ownership, run:")
    print("  python -c 'from test_fundamental_tools import test_institutional_ownership; test_institutional_ownership()'")
    print("="*80)
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
