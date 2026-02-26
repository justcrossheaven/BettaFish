"""
Financial Terminology Reference for Trade & Investment Analysis (Enhanced v2.0)

This module provides standardized financial terminology, search terms, and sector-specific
vocabulary for the Trade & Investment customization of BettaFish.

Used by: QueryEngine, InsightEngine, MediaEngine
Focus: US Technology/AI Sector + AI Infrastructure + Macro Context
"""

# ==============================================================================
# Financial Search Terms by Sentiment (Updated for 2026 AI Era)
# ==============================================================================

FINANCIAL_SEARCH_TERMS = {
    "bullish": [
        "calls", "moon", "rocket", "buy the dip", "undervalued",
        "breakout", "long", "accumulating", "value play", "upside potential",
        "price target raised", "strong buy", "outperform", "beat expectations",
        "margin expansion", "operating leverage", "moat widening"
    ],
    "bearish": [
        "puts", "short", "overvalued", "bubble", "crash",
        "breakdown", "sell-off", "correction", "downside risk", "overbought",
        "price target cut", "strong sell", "underperform", "miss expectations",
        "margin compression", "growth deceleration", "inventory glut"
    ],
    "neutral": [
        "hold", "fair value", "wait and see", "sideways", "range-bound",
        "neutral rating", "in-line with expectations", "priced in",
        "digest gains", "consolidation"
    ],
    
    # Platform-specific terminology (Updated)
    "reddit_specific": [
        "DD",           # Due Diligence
        "YOLO",         # You Only Live Once (high-risk trade)
        "diamond hands", # Holding through volatility
        "paper hands",   # Selling at first sign of trouble
        "tendies",      # Profits
        "bagholder",    # Left holding losing position
        "loss porn",    # Screenshots of large losses
        "BTFD",         # Buy The F***ing Dip
        "GUH",          # Sound of losing money instantly
        "regarded",     # (Slang) Highly risky/stupid trade
        "pricing in",   # "Is this priced in?"
        "AI bubble",    # Skepticism about AI valuation
        "GPU poor"      # Companies without enough compute
    ],
    "twitter_specific": [
        "$ticker",      # Cashtag
        "fintwit",      # Financial Twitter
        "thread",       # Long-form analysis
        "breaking",     # Breaking news
        "e/acc",        # Effective Accelerationism (Pro-AI growth ideology)
        "doomer",       # AI Safety/Risk focused (often bearish on speed)
        "rotation",     # Sector rotation (e.g., Tech to Value)
        "liquidity",    # Fed balance sheet discussions
        "chart crime"   # Misleading charts
    ],
    "stocktwits_specific": [
        "bullish/bearish ratio",
        "message volume spike",
        "trending tickers",
        "short squeeze alert"
    ]
}

# ==============================================================================
# Key Financial Metrics (Value Investing Enhanced)
# ==============================================================================

KEY_METRICS = [
    # Valuation Metrics
    "P/E ratio",            # Price-to-Earnings
    "Forward P/E",          # Future expected P/E
    "PEG ratio",            # P/E to Growth (Crucial for Tech)
    "P/S ratio",            # Price-to-Sales (For unprofitable growth)
    "P/B ratio",            # Price-to-Book
    "EV/EBITDA",            # Enterprise Value to EBITDA
    "FCF Yield",            # Free Cash Flow Yield (The Truth Metric)
    
    # Earnings & Profitability (Quality)
    "EPS",                  # Earnings Per Share
    "Revenue",              # Total Sales
    "Gross margin",         # Pricing power indicator
    "Operating margin",     # Operational efficiency
    "Net margin",           # Final profitability
    "ROIC",                 # Return on Invested Capital (Moat Metric)
    "ROCE",                 # Return on Capital Employed
    "FCF Conversion",       # EBITDA to FCF conversion rate
    
    # Balance Sheet Health
    "Net Debt/EBITDA",      # Leverage ratio
    "Current Ratio",        # Short-term liquidity
    "Quick Ratio",          # Acid test
    "Interest Coverage",    # Can they pay debt?
    
    # Growth Metrics
    "YoY growth",           # Year-over-Year
    "QoQ growth",           # Quarter-over-Quarter
    "Revenue guidance",     # Forward revenue projections
    "Book-to-Bill",         # Demand backlog indicator (Semis)
    "RPO",                  # Remaining Performance Obligations (SaaS backlog)
    
    # Market Data
    "Market cap", 
    "Volume", 
    "Float", 
    "Short interest", 
    "Days to cover",        # Squeeze potential
    "Beta",                 # Volatility vs Market
    
    # Technical Indicators
    "RSI", 
    "MACD", 
    "200-day MA",           # Long term trend
    "50-day MA",            # Medium term trend
    "Golden Cross",         # 50 crosses above 200
    "Death Cross"           # 50 crosses below 200
]

# ==============================================================================
# Accounting Red Flags (Forensic Analysis)
# ==============================================================================

ACCOUNTING_RED_FLAGS = [
    "DSO increase",                 # Days Sales Outstanding (Channel stuffing?)
    "Inventory turnover slowing",   # Product not selling?
    "DSI increase",                 # Days Sales of Inventory
    "Deferred revenue decline",     # Future growth slowing
    "Insider selling",              # Management dumping stock
    "Auditor resignation",          # Major warning
    "Restatement",                  # Correcting past errors
    "Goodwill impairment",          # Overpaid for acquisitions
    "Non-GAAP divergence",          # Gap between Adjusted and Real earnings widening
    "Related party transaction"     # Dealing with self
]

# ==============================================================================
# Tech Sector Companies - Expanded Watchlist
# ==============================================================================

TECH_SECTOR_COMPANIES = {
    # Tier 1: The "Mag 7" + AI Leaders
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors", "sub_sector": "AI Compute"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Software", "sub_sector": "Cloud/AI"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Internet", "sub_sector": "Search/AI"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "E-commerce", "sub_sector": "Cloud/Logistics"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Social Media", "sub_sector": "AdTech/Llama"},
    "AAPL": {"name": "Apple Inc.", "sector": "Consumer Electronics", "sub_sector": "Edge AI"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Auto", "sub_sector": "Robotics/FSD"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "sub_sector": "Networking"},
    
    # Tier 2: The Challengers & Foundries
    "AMD": {"name": "Advanced Micro Devices", "sector": "Semiconductors", "sub_sector": "AI/CPU"},
    "INTC": {"name": "Intel Corporation", "sector": "Semiconductors", "sub_sector": "Foundry/CPU"},
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Semiconductors", "sub_sector": "Foundry"},
    "ARM": {"name": "Arm Holdings", "sector": "Semiconductors", "sub_sector": "IP Design"},
    "MU": {"name": "Micron Technology", "sector": "Semiconductors", "sub_sector": "Memory (HBM)"},
    
    # Tier 3: AI Infrastructure (Power & Cooling - The Hidden Plays)
    "SMCI": {"name": "Super Micro Computer", "sector": "Hardware", "sub_sector": "Servers/Liquid Cooling"},
    "VRT": {"name": "Vertiv Holdings", "sector": "Industrials", "sub_sector": "Data Center Cooling"},
    "ANET": {"name": "Arista Networks", "sector": "Networking", "sub_sector": "Ethernet"},
    "CEG": {"name": "Constellation Energy", "sector": "Utilities", "sub_sector": "Nuclear Power"},
    
    # Tier 4: Software & Data
    "PLTR": {"name": "Palantir Technologies", "sector": "Software", "sub_sector": "Big Data/Defense"},
    "SNOW": {"name": "Snowflake Inc.", "sector": "Software", "sub_sector": "Data Cloud"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Software", "sub_sector": "SaaS"},
    "ORCL": {"name": "Oracle Corporation", "sector": "Software", "sub_sector": "Cloud/Database"}
}

# Simplified ticker list
TECH_TICKER_LIST = list(TECH_SECTOR_COMPANIES.keys())

# ==============================================================================
# Macro & Sector Context Search Terms
# ==============================================================================

MACRO_CONTEXT_TERMS = [
    "10-year Treasury yield",   # Risk-free rate (valuation gravity)
    "Fed funds rate",           # Cost of capital
    "CPI inflation",            # Inflation data
    "Powell speech",            # Fed sentiment
    "Semiconductor cycle",      # Sector cyclicality
    "CapEx spending",           # Cloud giant spending plans
    "Geopolitical tension Taiwan", # Supply chain risk
    "Export controls China"     # Regulatory risk
]

# ==============================================================================
# Data Sources by Priority
# ==============================================================================

FINANCIAL_DATA_SOURCES = {
    "tier_1_official": [
        "SEC EDGAR filings (10-K, 10-Q, 8-K)",
        "Company Investor Relations (IR) website",
        "Earnings Call Transcripts",
        "Federal Reserve Economic Data (FRED)"
    ],
    "tier_2_news": [
        "Bloomberg Terminal/News",
        "Reuters Finance",
        "Wall Street Journal (WSJ)",
        "Financial Times (FT)",
        "CNBC Pro"
    ],
    "tier_3_analysis": [
        "Seeking Alpha (Transcripts & Analysis)",
        "Morningstar",
        "Barron's",
        "Benzinga Pro"
    ],
    "tier_4_social_sentiment": [
        "Twitter/X (Fintwit)",
        "Reddit (r/stocks, r/investing, r/wallstreetbets)",
        "StockTwits",
        "Blind (Tech employee sentiment)",
        "Substack (Techno-optimists)"
    ]
}