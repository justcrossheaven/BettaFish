"""
DCF (Discounted Cash Flow) Model Scaffolding
This prevents LLM hallucination by making the LLM provide assumptions
while Python does the rigorous math.

The LLM fills in assumptions based on analysis; Python computes the valuation.
Output: Fair value per share with bull/base/bear scenarios.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import math


@dataclass
class DCFAssumptions:
    """
    Input assumptions for DCF model.
    The LLM should fill these based on fundamental analysis.
    """
    # Company identification
    ticker: str
    company_name: str
    
    # Base year data (most recent fiscal year)
    current_revenue: float  # In millions
    current_fcf: float  # Free Cash Flow in millions (or will be calculated)
    current_operating_margin: float  # As decimal (e.g., 0.25 for 25%)
    shares_outstanding: float  # In millions
    
    # Growth assumptions (5-year projection period)
    revenue_growth_rates: List[float]  # Year 1-5, as decimals
    
    # Margin assumptions
    terminal_operating_margin: float  # Long-term steady-state margin
    
    # Capital intensity
    capex_percent_of_revenue: float  # As decimal
    nwc_percent_of_revenue: float  # Net Working Capital change as % of revenue
    
    # Discount rate components
    risk_free_rate: float  # 10Y Treasury yield
    equity_risk_premium: float  # Market risk premium (typically 5-7%)
    beta: float  # Stock's beta
    
    # Or use WACC directly
    wacc: Optional[float] = None  # Weighted Average Cost of Capital
    
    # Terminal value assumptions
    terminal_growth_rate: float = 0.025  # Perpetual growth (typically 2-3%)
    
    # Tax rate
    tax_rate: float = 0.21  # Corporate tax rate (US federal = 21%)
    
    def calculate_wacc(self) -> float:
        """Calculate WACC using CAPM if not provided directly"""
        if self.wacc is not None:
            return self.wacc
        
        # CAPM: Cost of Equity = Risk Free Rate + Beta * Equity Risk Premium
        cost_of_equity = self.risk_free_rate + (self.beta * self.equity_risk_premium)
        
        # For simplicity, assuming 100% equity financing (common for tech companies)
        # In practice, you'd include cost of debt weighted by capital structure
        return cost_of_equity
    
    def __post_init__(self):
        """Validation"""
        if len(self.revenue_growth_rates) != 5:
            raise ValueError("revenue_growth_rates must be a list of 5 values (year 1-5)")
        
        if self.terminal_growth_rate >= self.calculate_wacc():
            raise ValueError("Terminal growth rate must be less than WACC")


class DCFModel:
    """
    Rigorous DCF valuation model.
    Prevents LLM from hallucinating valuations by forcing explicit assumptions.
    """
    
    def __init__(self, assumptions: DCFAssumptions):
        self.assumptions = assumptions
        self.wacc = assumptions.calculate_wacc()
        self.projections = []
        self.terminal_value = 0
        self.enterprise_value = 0
        self.fair_value_per_share = 0
    
    def project_free_cash_flows(self) -> List[Dict]:
        """
        Project Free Cash Flows for 5 years.
        
        FCF = NOPAT + D&A - CapEx - Change in NWC
        Simplified: FCF = Revenue * Operating Margin * (1 - Tax Rate) - CapEx - NWC Change
        """
        projections = []
        current_revenue = self.assumptions.current_revenue
        
        for year in range(1, 6):
            # Project revenue
            growth_rate = self.assumptions.revenue_growth_rates[year - 1]
            revenue = current_revenue * (1 + growth_rate)
            
            # Calculate operating margin (gradual improvement to terminal margin)
            # Linear interpolation from current to terminal
            if year == 1:
                operating_margin = self.assumptions.current_operating_margin
            else:
                # Gradual convergence to terminal margin
                weight = (year - 1) / 5
                operating_margin = (
                    self.assumptions.current_operating_margin * (1 - weight) +
                    self.assumptions.terminal_operating_margin * weight
                )
            
            # NOPAT (Net Operating Profit After Tax)
            nopat = revenue * operating_margin * (1 - self.assumptions.tax_rate)
            
            # CapEx
            capex = revenue * self.assumptions.capex_percent_of_revenue
            
            # Change in Net Working Capital
            revenue_increase = revenue - current_revenue
            nwc_change = revenue_increase * self.assumptions.nwc_percent_of_revenue
            
            # Free Cash Flow
            fcf = nopat - capex - nwc_change
            
            # Discount factor
            discount_factor = 1 / ((1 + self.wacc) ** year)
            present_value = fcf * discount_factor
            
            projections.append({
                'year': year,
                'revenue': revenue,
                'operating_margin': operating_margin,
                'nopat': nopat,
                'capex': capex,
                'nwc_change': nwc_change,
                'fcf': fcf,
                'discount_factor': discount_factor,
                'pv_fcf': present_value
            })
            
            current_revenue = revenue
        
        self.projections = projections
        return projections
    
    def calculate_terminal_value(self) -> float:
        """
        Calculate Terminal Value using Gordon Growth Model.
        
        TV = FCF_terminal * (1 + g) / (WACC - g)
        Where g = terminal growth rate
        """
        # Terminal year FCF (year 5)
        terminal_fcf = self.projections[-1]['fcf']
        
        # Terminal Value
        g = self.assumptions.terminal_growth_rate
        tv = terminal_fcf * (1 + g) / (self.wacc - g)
        
        # Discount Terminal Value to present
        discount_factor = 1 / ((1 + self.wacc) ** 5)
        pv_terminal_value = tv * discount_factor
        
        self.terminal_value = pv_terminal_value
        return pv_terminal_value
    
    def calculate_enterprise_value(self) -> float:
        """
        Enterprise Value = PV of Projected FCFs + PV of Terminal Value
        """
        pv_fcfs = sum(p['pv_fcf'] for p in self.projections)
        self.enterprise_value = pv_fcfs + self.terminal_value
        return self.enterprise_value
    
    def calculate_equity_value_per_share(self) -> float:
        """
        Equity Value = Enterprise Value (assuming no net debt for simplicity)
        Fair Value Per Share = Equity Value / Shares Outstanding
        
        Note: In practice, you'd adjust for net debt, minority interests, etc.
        """
        equity_value = self.enterprise_value  # Simplified (no debt adjustment)
        fair_value = equity_value / self.assumptions.shares_outstanding
        
        self.fair_value_per_share = fair_value
        return fair_value
    
    def run_valuation(self) -> Dict:
        """
        Execute full DCF valuation.
        
        Returns:
            Dictionary with:
            - fair_value_per_share
            - enterprise_value
            - terminal_value
            - projections
            - wacc
            - assumptions summary
        """
        # Run the DCF
        self.project_free_cash_flows()
        self.calculate_terminal_value()
        self.calculate_enterprise_value()
        self.calculate_equity_value_per_share()
        
        # Calculate value breakdown
        pv_fcfs = sum(p['pv_fcf'] for p in self.projections)
        tv_percent = (self.terminal_value / self.enterprise_value * 100) if self.enterprise_value > 0 else 0
        
        return {
            'ticker': self.assumptions.ticker,
            'fair_value_per_share': self.fair_value_per_share,
            'enterprise_value': self.enterprise_value,
            'pv_projected_fcfs': pv_fcfs,
            'terminal_value': self.terminal_value,
            'terminal_value_percent': tv_percent,
            'wacc': self.wacc,
            'projections': self.projections,
            'assumptions': self.assumptions
        }


class DCFScenarioAnalysis:
    """
    Run Bull/Base/Bear scenario analysis.
    """
    
    @staticmethod
    def create_scenarios(
        base_assumptions: DCFAssumptions
    ) -> Dict[str, DCFAssumptions]:
        """
        Create three scenarios from base assumptions.
        
        Bull: Higher growth, better margins, lower WACC
        Base: As provided
        Bear: Lower growth, compressed margins, higher WACC
        """
        import copy
        
        bull = copy.deepcopy(base_assumptions)
        bear = copy.deepcopy(base_assumptions)
        
        # Bull case: +20% growth, +200bps margin, -100bps WACC
        bull.revenue_growth_rates = [r * 1.2 for r in bull.revenue_growth_rates]
        bull.terminal_operating_margin = min(0.95, bull.terminal_operating_margin + 0.02)
        if bull.wacc is not None:
            bull.wacc = max(0.01, bull.wacc - 0.01)
        else:
            bull.beta = max(0.5, bull.beta - 0.2)
        
        # Bear case: -30% growth, -300bps margin, +200bps WACC
        bear.revenue_growth_rates = [r * 0.7 for r in bear.revenue_growth_rates]
        bear.terminal_operating_margin = max(0.05, bear.terminal_operating_margin - 0.03)
        if bear.wacc is not None:
            bear.wacc = bear.wacc + 0.02
        else:
            bear.beta = bear.beta + 0.3
        
        return {
            'bear': bear,
            'base': base_assumptions,
            'bull': bull
        }
    
    @staticmethod
    def run_scenario_analysis(
        base_assumptions: DCFAssumptions
    ) -> Dict[str, Dict]:
        """
        Run DCF for Bull/Base/Bear scenarios.
        
        Returns:
            Dictionary with results for each scenario
        """
        scenarios = DCFScenarioAnalysis.create_scenarios(base_assumptions)
        results = {}
        
        for scenario_name, assumptions in scenarios.items():
            model = DCFModel(assumptions)
            results[scenario_name] = model.run_valuation()
        
        return results


def print_dcf_results(results: Dict, current_price: Optional[float] = None):
    """Pretty print DCF results"""
    print(f"\n{'='*70}")
    print(f"DCF Valuation Results: {results['ticker']}")
    print(f"{'='*70}\n")
    
    print(f"Fair Value Per Share: ${results['fair_value_per_share']:.2f}")
    if current_price:
        upside = (results['fair_value_per_share'] - current_price) / current_price * 100
        print(f"Current Price: ${current_price:.2f}")
        print(f"Implied Upside/Downside: {upside:+.1f}%\n")
    
    print(f"Enterprise Value: ${results['enterprise_value']:,.0f}M")
    print(f"PV of Projected FCFs (Year 1-5): ${results['pv_projected_fcfs']:,.0f}M")
    print(f"Terminal Value: ${results['terminal_value']:,.0f}M ({results['terminal_value_percent']:.1f}% of EV)")
    print(f"WACC: {results['wacc']*100:.2f}%\n")
    
    print("5-Year FCF Projections:")
    print(f"{'Year':<6} {'Revenue':>12} {'Margin':>10} {'FCF':>12} {'PV of FCF':>12}")
    print("-" * 70)
    for proj in results['projections']:
        print(f"{proj['year']:<6} ${proj['revenue']:>11,.0f}M "
              f"{proj['operating_margin']*100:>9.1f}% "
              f"${proj['fcf']:>11,.0f}M ${proj['pv_fcf']:>11,.0f}M")
    
    print(f"{'='*70}\n")


def print_scenario_analysis(
    scenario_results: Dict[str, Dict],
    current_price: Optional[float] = None
):
    """Pretty print scenario analysis"""
    print(f"\n{'='*70}")
    print(f"DCF Scenario Analysis: {scenario_results['base']['ticker']}")
    print(f"{'='*70}\n")
    
    print(f"{'Scenario':<15} {'Fair Value':>15} {'Upside/Downside':>20}")
    print("-" * 70)
    
    for scenario in ['bear', 'base', 'bull']:
        result = scenario_results[scenario]
        fv = result['fair_value_per_share']
        
        upside_str = ""
        if current_price:
            upside = (fv - current_price) / current_price * 100
            upside_str = f"{upside:+.1f}%"
        
        emoji = "🔴" if scenario == 'bear' else ("🟡" if scenario == 'base' else "🟢")
        print(f"{emoji} {scenario.upper():<12} ${fv:>14.2f} {upside_str:>20}")
    
    if current_price:
        print(f"\nCurrent Price: ${current_price:.2f}")
        
        base_fv = scenario_results['base']['fair_value_per_share']
        bull_fv = scenario_results['bull']['fair_value_per_share']
        bear_fv = scenario_results['bear']['fair_value_per_share']
        
        if current_price < bear_fv:
            print("✅ Stock appears UNDERVALUED even in Bear case")
        elif current_price > bull_fv:
            print("⚠️  Stock appears OVERVALUED even in Bull case")
        elif current_price < base_fv:
            print("👍 Stock appears UNDERVALUED vs Base case")
        else:
            print("👎 Stock appears OVERVALUED vs Base case")
    
    print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    # Example: NVIDIA DCF (simplified numbers for demonstration)
    assumptions = DCFAssumptions(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        current_revenue=60000,  # $60B (FY2024)
        current_fcf=15000,  # $15B
        current_operating_margin=0.55,  # 55%
        shares_outstanding=2460,  # 2.46B shares
        revenue_growth_rates=[0.35, 0.30, 0.25, 0.20, 0.15],  # Decelerating growth
        terminal_operating_margin=0.50,  # 50% long-term
        capex_percent_of_revenue=0.05,  # 5% of revenue
        nwc_percent_of_revenue=0.02,  # 2% of revenue growth
        risk_free_rate=0.045,  # 4.5% (10Y Treasury)
        equity_risk_premium=0.06,  # 6%
        beta=1.5,  # Tech stock
        terminal_growth_rate=0.03,  # 3% perpetual
        tax_rate=0.21
    )
    
    # Base case
    print("Running Base Case DCF...")
    model = DCFModel(assumptions)
    results = model.run_valuation()
    print_dcf_results(results, current_price=125.00)
    
    # Scenario analysis
    print("\nRunning Scenario Analysis...")
    scenario_results = DCFScenarioAnalysis.run_scenario_analysis(assumptions)
    print_scenario_analysis(scenario_results, current_price=125.00)
