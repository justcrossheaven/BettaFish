# BettaFish Trade & Investment Customization Plan

Transform BettaFish from a Chinese public opinion monitor into a **US Trade & Investment** analysis platform focused on the **Technology/AI sector**.

## User Review Required

> [!IMPORTANT]
> This is a significant architectural change. Please review the proposed changes carefully.

**Key Decisions:**
1. **Keeping Douyin & XHS** - Retained **only** for supply-chain leaks and China market sentiment for US tech companies (see Perception Layer below)
2. **Open Source First** - Prioritize free/open-source scrapers (`twikit`, `PRAW`, `newspaper4k`) over paid APIs
3. **Budget constraints** - Plan targets <$20/month (primarily for Tavily/LLM costs)
4. **Perception vs. Decision Firewall** - Social media sentiment informs but does NOT drive investment decisions

---

## Architectural Overview

> [!NOTE]
> This architecture separates **narrative awareness** from **investment judgement** to prevent social media noise from contaminating financial analysis.

### Three-Layer Model

```
[Perception Layer]  ─── Narrative Radar Agent (Twitter / Reddit / Douyin / XHS)
        │
        ▼ (structured data only, no recommendations)
[Analysis Layer]    ─── Financial Statements Agent
                    ─── Management & Capital Allocation Agent
                    ─── News & Event Analysis Agent
        │
        ▼ (escalated items only)
[Judgement Layer]   ─── Value Investor Judge
```

### Layer Responsibilities

| Layer | Engine | Role | Output |
|-------|--------|------|--------|
| **Perception** | `InsightEngine` | Environment scanner, NOT decision-maker | Hot-Topic Matrix (structured) |
| **Analysis** | `QueryEngine` + `MediaEngine` | Financial research, news verification | Factual analysis report |
| **Judgement** | Future / Manual | Investment thesis, risk assessment | Buy/Sell/Hold (if any) |

### Perception Layer Role Definition

**Responsibilities:**
- Detect current market discussion themes
- Identify rapidly spreading narratives
- Surface emerging risks or controversies
- Summarize market attention and sentiment distribution

**Explicit Exclusions (Firewall):**
- ❌ No buy / sell / hold opinions
- ❌ No judgement on narrative correctness
- ❌ No price prediction
- ❌ No override of fundamental analysis

### Chinese Source Clarification

| Source Type | Usage | Rationale |
|-------------|-------|-----------|
| **Douyin / XHS** | ✅ Retained (limited) | Supply-chain rumors, China market sentiment for US tech |
| **Weibo / Bilibili / Zhihu / Tieba** | ❌ Excluded | General Chinese social media, not relevant to US investment |

---

## Proposed Changes

### Phase 1: Core Improvements (503 Error & Caching)

---

#### [MODIFY] [retry_helper.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/utils/retry_helper.py)

**Improve 503 error handling:**
- Add specific detection for HTTP 503 "model overloaded" errors
- Implement longer backoff specifically for 503 errors (up to 5 minutes between retries)
- Add jitter (random delay) to avoid thundering herd when model becomes available

```python
# Add to LLM_RETRY_CONFIG
LLM_RETRY_CONFIG = RetryConfig(
    max_retries=8,           # Increase from 6
    initial_delay=10.0,      # Start with 10s (faster recovery)
    backoff_factor=2.0,      # Doubles each time: 10s → 20s → 40s → 80s
    max_delay=120.0,         # Cap at 2 minutes max
    jitter=True              # NEW: Add random jitter
)
# Retry sequence: 10s, 20s, 40s, 80s, 120s, 120s, 120s, 120s
```

---

#### [MODIFY] LLM Clients - Implement Gemini Native Context Caching

**Use Gemini's built-in context caching (both implicit and explicit):**

Reference: [Gemini Context Caching Docs](https://ai.google.dev/gemini-api/docs/caching?lang=python)

**1. Implicit Caching (Automatic - No Code Changes Needed):**
- Enabled by default since May 2025 for Gemini models
- Automatically passes on cost savings when requests hit caches
- To increase cache hit rate:
  - Put large/common content at the **beginning** of prompts
  - Send requests with similar prefixes in short time windows
- Check `response.usage_metadata` for cache hit statistics

**2. Explicit Caching (Code Changes Required):**

Modify [InsightEngine/llms/base.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/InsightEngine/llms/base.py) and similar files:

```python
import google.generativeai as genai
from google.generativeai import caching

# Create a cache for frequently used system prompts
cache = caching.CachedContent.create(
    model="gemini-2.0-flash-001",
    display_name="trade_investment_system_prompt",
    system_instruction="You are a Trade & Investment analyst...",
    contents=[large_reference_document],  # Optional: large docs
    ttl=datetime.timedelta(hours=1)  # Cache for 1 hour
)

# Use cached content in subsequent requests
model = genai.GenerativeModel.from_cached_content(cached_content=cache)
response = model.generate_content("Analyze NVDA stock...")
```

**Best Use Cases for Explicit Caching:**
- Large system instructions (our Trade & Investment prompts)
- Recurring queries against financial document sets
- Repetitive analysis patterns

**Cost Impact:**
- Cached tokens billed at **reduced rate** when included in subsequent prompts
- Storage cost based on TTL duration
- Can significantly reduce costs for repeated similar queries

---

### Phase 1.5: Prompt & Query Customization for Trade & Investment

> [!IMPORTANT]
> **Yes, prompts need significant changes!** Current prompts are heavily tailored for Chinese 舆情 (public opinion) analysis and need to be rewritten for Trade & Investment focus.

---

#### Current Prompt Issues (Must Change)

| Issue | Current State | Required Change |
|-------|---------------|-----------------|
| **Language** | All Chinese, with Chinese slang/expressions | Switch to English with financial terminology |
| **Context** | "舆情分析师" (public opinion analyst) | "Financial/Investment Analyst" |
| **Platform examples** | Weibo, Bilibili, Douyin terminology | Twitter, Reddit, Bloomberg terminology |
| **Search guidance** | Chinese internet slang ("yyds", "666", "绝了") | Financial terms ("bullish", "earnings beat", "guidance") |
| **Report structure** | Social sentiment, public opinion tables | Financial metrics, P/E ratios, analyst ratings |
| **Focus** | Public reaction, social spread | Market impact, investment thesis, risk factors |

---

#### [MODIFY] [QueryEngine/prompts/prompts.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/prompts/prompts.py)

**Key Changes:**
- Role: "深度研究助手" → "Senior Trade & Investment Research Analyst"
- Focus: News search → Financial news, earnings reports, SEC filings
- Language: Chinese → English (with Chinese option for XHS/Douyin sources)
- Report structure: Add sections for:
  - Key Financial Metrics (P/E, Revenue, EPS)
  - Analyst Ratings & Price Targets
  - Risk Factors
  - Competitive Landscape
  - Investment Thesis

**New Search Query Guidance:**
```python
# Instead of:
"武大" or "武汉大学怎么了"

# Use:
"NVDA earnings Q4 2026" or "NVIDIA revenue guidance"
"AMD vs NVDA market share" or "$NVDA price target"
"tech sector outlook 2026" or "AI chip demand forecast"
```

---

#### [MODIFY] [InsightEngine/prompts/prompts.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/InsightEngine/prompts/prompts.py)

**Role Redefinition (Perception Layer):**
- Current: "舆情分析师" (public opinion analyst)
- New: "Narrative Radar Agent" — environment scanner, NOT decision-maker

**Key Changes:**
- Remove Chinese platform terminology (Weibo, B站, 知乎, 贴吧)
- Add Twitter/Reddit/StockTwits sentiment analysis patterns
- Focus on: retail sentiment, institutional holdings, insider trading signals

**New Structured Output: Hot-Topic Matrix**

Replace free-form narrative summaries with structured JSON output:

```python
output_schema_hot_topic_matrix = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "entity": {"type": "string", "description": "Company / sector / individual"},
            "narrative_direction": {"enum": ["positive", "negative", "mixed"]},
            "emotional_intensity": {"enum": ["low", "medium", "high"]},
            "spread_velocity": {"enum": ["new", "ongoing", "fading"]},
            "primary_platform": {"type": "string"},
            "first_appearance": {"type": "boolean"},
            "escalation_required": {"type": "boolean"}
        },
        "required": ["topic", "entity", "narrative_direction", "escalation_required"]
    }
}
```

**Non-Decision Constraints (Add to System Prompts):**

```
MANDATORY RULES:
1. Hot topics do NOT imply correctness
2. Strong sentiment does NOT imply importance
3. You are PROHIBITED from providing:
   - Buy / Sell / Hold recommendations
   - Price predictions
   - Judgement on narrative truth or falsehood
4. Your role is to REPORT what is being discussed, NOT what is true
```

**Escalation Mechanism:**

Add the following to `SYSTEM_PROMPT_FIRST_SUMMARY` and `SYSTEM_PROMPT_REFLECTION_SUMMARY`:

```
Set "escalation_required": true ONLY when ANY of the following conditions are met:
- A new theme emerges that was not previously tracked
- Narrative is spreading rapidly (velocity = "new" AND intensity = "high")
- Topic touches fundamentals (earnings, guidance, management changes)
- Topic involves governance or regulatory concerns
- Topic involves supply-chain disruption or geopolitical risk

Only escalated items will proceed to the Analysis and Judgement layers.
```

**New Platform Language Examples:**
```python
# Instead of:
"微博热搜", "B站弹幕", "知乎问答"

# Use:
"r/wallstreetbets DD", "$NVDA trending on Twitter"
"fintwit sentiment", "StockTwits bearish/bullish ratio"
```

---

#### [MODIFY] [MediaEngine/prompts/prompts.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MediaEngine/prompts/prompts.py)

**Key Changes:**
- Multimodal focus: earnings call transcripts, analyst presentations, charts
- Visual analysis: stock chart patterns, company logos, product images
- Data integration: real-time stock prices, volume, market cap

---

#### [NEW] Trade & Investment Specific Terminology Reference

Create `prompts/financial_terminology.py`:

```python
FINANCIAL_SEARCH_TERMS = {
    "bullish": ["calls", "moon", "rocket", "buy the dip", "undervalued"],
    "bearish": ["puts", "short", "overvalued", "bubble", "crash"],
    "neutral": ["hold", "fair value", "wait and see", "sideways"],
    "reddit_specific": ["DD", "YOLO", "diamond hands", "paper hands", "tendies"],
    "twitter_specific": ["$ticker", "fintwit", "CT (Crypto Twitter)", "thread"]
}

KEY_METRICS = [
    "P/E ratio", "EPS", "Revenue", "Earnings", "Guidance",
    "Market cap", "Volume", "52-week high/low", "RSI", "MACD"
]

TECH_SECTOR_COMPANIES = [
    "NVDA", "AMD", "INTC", "MSFT", "GOOGL", "META", "AAPL", 
    "AMZN", "TSLA", "TSM", "AVGO", "QCOM"
]
```

---

### Phase 2: Platform Integration Changes

---

#### [MODIFY] [MindSpider/config.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MindSpider/config.py)

**Disable unused Chinese platforms:**
```python
ENABLED_PLATFORMS = ["douyin", "xhs"]  # Remove: weibo, kuaishou, bilibili, tieba, zhihu
```

---

#### [NEW] [QueryEngine/tools/twitter_search.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/tools/twitter_search.py)

**Twitter/X integration via `twikit` (Open Source):**
- Uses internal API (web simulation) to avoid high API costs
- Requires Twitter account credentials (cookies)
- Focus on tech/AI influencers ($NVDA, $AMD)

```python
import twikit

class TwitterSearchClient:
    """Twitter/X search via twikit (Reverse Engineered API)."""
    
    def __init__(self, username, email, password):
        self.client = twikit.Client('en-US')
        # Login logic with cookie persistence
        ...
    
    async def search_tweets(self, query: str, category='Top') -> List[TweetResult]:
        """Search tweets using web client simulation."""
        tweets = await self.client.search_tweet(query,product=category)
        return [self._parse_tweet(t) for t in tweets]
```

---

#### [NEW] [QueryEngine/tools/reddit_search.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/tools/reddit_search.py)

**Reddit API integration:**
- Official Reddit API (free tier: 100 requests/minute)
- Focus subreddits: r/wallstreetbets, r/stocks, r/investing, r/technology, r/nvidia, r/AMD, r/artificial
- Filter by upvotes, comments, awards

```python
class RedditSearchClient:
    """Reddit search via official API."""
    
    FINANCE_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options"]
    TECH_SUBREDDITS = ["technology", "nvidia", "AMD", "artificial", "MachineLearning"]
    
    def search_posts(self, query: str, subreddits: List[str] = None) -> List[RedditPost]:
        """Search Reddit posts with tech/finance focus."""
        ...
    
    def get_hot_posts(self, subreddit: str, limit: int = 25) -> List[RedditPost]:
        """Get trending posts from specific subreddit."""
        ...
```

---

#### [NEW] [QueryEngine/tools/google_search.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/tools/google_search.py)

**Google Search/News integration:**
- Use SerpAPI (affordable: $50/month for 5,000 searches) or Google Custom Search API
- Focus on financial news, company announcements
- Filter by date, source credibility

```python
class GoogleSearchClient:
    """Google Search via SerpAPI or Custom Search API."""
    
    def search_news(self, query: str, days_back: int = 7) -> List[NewsResult]:
        """Search Google News with date filtering."""
        ...
    
    def search_financial(self, ticker: str) -> List[NewsResult]:
        """Search financial news for specific ticker."""
        ...
```

---

#### [NEW] [QueryEngine/tools/financial_data.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/tools/financial_data.py)

**Financial data integration:**
- Yahoo Finance (free, via yfinance library)
- Basic stock data: price, volume, market cap, P/E ratio
- Company news and earnings dates

```python
class FinancialDataClient:
    """Financial data via Yahoo Finance API."""
    
    TECH_WATCHLIST = ["NVDA", "AMD", "MSFT", "GOOGL", "META", "TSLA", "AMZN", "AAPL"]
    
    def get_stock_info(self, ticker: str) -> StockInfo:
        """Get current stock data and key metrics."""
        ...
    
    def get_company_news(self, ticker: str, days_back: int = 7) -> List[NewsResult]:
        """Get recent news for ticker."""
        ...
    
    def get_earnings_calendar(self, tickers: List[str]) -> List[EarningsEvent]:
        """Get upcoming earnings dates."""
        ...
```

---

### Phase 2.5: Cost-Effective Data Acquisition (New Modules)

> [!TIP]
> To significantly reduce API costs (from ~$50/mo to near zero), we will implement open-source scrapers and reverse-engineered clients instead of paid official APIs.

#### [NEW] [MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/twitter/](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/twitter/)

**Module: Twitter Scraper (using `twikit`)**
- **Repo Reference**: `d60/twikit`
- **Mechanism**: Simulates Twitter web client (Internal API) to fetch tweets without official API key.
- **Features**: Search tweets, get user timeline, thread replies.
- **Cost**: Free.
- **Implementation**:
  - Implement `TwitterClient` wrapping `twikit`.
  - Handle cookie management/login (similar to existing MediaCrawler logic).

#### [NEW] [MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/reddit/](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/reddit/)

**Module: Reddit Scraper (using `URS` or `PRAW`)**
- **Repo Reference**: `JosephLai241/URS` (Universal Reddit Scraper) or official `PRAW`.
- **Mechanism**: 
  - `PRAW`: Official API (Free tier is generous: 100 req/min). Stable and reliable.
  - `URS`: Powerful CLI tool for bulk archiving subreddits.
- **Recommendation**: Use `PRAW` for real-time monitoring, `URS` for historical deep dives.
- **Cost**: Free.

#### [NEW] [MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/news/](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MindSpider/DeepSentimentCrawling/MediaCrawler/media_platform/news/)

**Module: News Extractor (using `newspaper4k`)**
- **Repo Reference**: `AndyTheFactory/newspaper4k`
- **Mechanism**: Extracts structure (Title, Author, Body, Date) from any news URL.
- **Workflow**:
  1. Use search engine (Tavily/Google) to get URLs.
  2. Pass URLs to `newspaper4k` to scrape full content.
- **Cost**: Free (only search engine costs apply, parsing is local).

---

### Phase 3: Configuration Updates

---

#### [MODIFY] [.env.example](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/.env.example)

**Add new API keys:**
```env
# ================== Western Search APIs ====================
# Twitter/X (twikit - requires account)
TWITTER_USERNAME=your_username
TWITTER_EMAIL=your_email
TWITTER_PASSWORD=your_password
TWITTER_COOKIES_PATH=cookies.json

# Reddit API (official)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=BettaFish/1.0

# Google Search (SerpAPI or Custom Search)
GOOGLE_SEARCH_PROVIDER=serpapi  # Options: serpapi, custom_search
SERPAPI_KEY=your_serpapi_key
# OR
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_api_key
GOOGLE_CUSTOM_SEARCH_CX=your_search_engine_id

# ================== Sector Focus ====================
# Default watchlist for automated monitoring
DEFAULT_WATCHLIST=NVDA,AMD,MSFT,GOOGL,META,TSLA
FOCUS_SECTOR=technology,AI
```

---

#### [MODIFY] [config.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/config.py)

**Add new settings to Settings class:**
```python
# Western API settings
TWITTER_USERNAME: Optional[str] = Field(None, description="Twitter username")
TWITTER_EMAIL: Optional[str] = Field(None, description="Twitter email")
TWITTER_PASSWORD: Optional[str] = Field(None, description="Twitter password")
TWITTER_COOKIES_PATH: str = Field("cookies.json", description="Path to save/load Twitter cookies")
REDDIT_CLIENT_ID: Optional[str] = Field(None, description="Reddit client ID")
REDDIT_CLIENT_SECRET: Optional[str] = Field(None, description="Reddit client secret")
REDDIT_USER_AGENT: str = Field("BettaFish/1.0", description="Reddit user agent")
SERPAPI_KEY: Optional[str] = Field(None, description="SerpAPI key for Google Search")
DEFAULT_WATCHLIST: str = Field("NVDA,AMD,MSFT,GOOGL,META", description="Default stock watchlist")
FOCUS_SECTOR: str = Field("technology,AI", description="Focus sector for analysis")
```

---

#### [MODIFY] [QueryEngine/prompts/prompts.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/QueryEngine/prompts/prompts.py)

**Update prompts for Trade & Investment focus:**
- Add financial analysis context
- Focus on market sentiment, earnings, analyst opinions
- Include tech/AI sector terminology

---

#### [MODIFY] [MediaEngine/tools/search.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/MediaEngine/tools/search.py)

**Add Western search priority:**
- Route queries to appropriate search provider based on content
- Use Tavily for international news (already configured)
- Add fallback chain: Tavily → Google → Bocha

---

### Phase 4: Future Enhancements (Lower Priority)

---

#### [NEW] [utils/watchlist_monitor.py](file:///c:/Users/John%20Jia/Desktop/Public%20Opinion%20Monitor/BettaFish/utils/watchlist_monitor.py)

**Automated ticker monitoring (future):**
- Scheduled checks for watchlist stocks
- Alert on price movements, news, or sentiment changes
- Integration with notification system (email/webhook)

---

## Summary of New Dependencies

Add to `requirements.txt` (or install via pip):
```
# Twitter
twikit>=1.0.0

# Reddit
praw>=7.7.0

# News
newspaper4k>=0.9.0
lxml_html_clean
```

---

## Budget Estimation (Revised)

| Service | Old Plan Cost | **New Plan Cost** | Notes |
|---------|---------------|-------------------|-------|
| Twitter | $20-40/mo | **$0** | Using `twikit` (no API key needed) |
| Reddit | Free | **Free** | Using `PRAW`/`URS` |
| News Parsing | N/A | **Free** | Using `newspaper4k` |
| Search API | $50/mo | **$10-20/mo** | Only needed for discovery (Tavily) |
| **Total** | **~$90/mo** | **<$20/mo** | **Significant Savings** |

**Alternative to SerpAPI:** Use Tavily (you already have) + Google Custom Search API ($5/1,000 queries after 100 free/day)

---

## Verification Plan

### Automated Tests

The project has existing tests in `tests/` directory:
- `test_monitor.py` - ForumEngine tests
- `test_report_engine_sanitization.py` - ReportEngine tests

**New tests to add:**
```bash
# Run existing tests
python -m pytest tests/ -v

# New integration tests for Western APIs (to be created)
python -m pytest tests/test_twitter_search.py -v
python -m pytest tests/test_reddit_search.py -v
python -m pytest tests/test_financial_data.py -v
```

### Manual Verification

1. **Test 503 retry improvements:**
   - Run the system during peak hours
   - Monitor logs for retry behavior
   - Verify exponential backoff with jitter

2. **Test new search integrations:**
   ```bash
   # Test Twitter search
   python -c "from QueryEngine.tools.twitter_search import TwitterSearchClient; c = TwitterSearchClient(); print(c.search_tweets('NVIDIA AI'))"
   
   # Test Reddit search
   python -c "from QueryEngine.tools.reddit_search import RedditSearchClient; c = RedditSearchClient(); print(c.get_hot_posts('wallstreetbets'))"
   
   # Test financial data
   python -c "from QueryEngine.tools.financial_data import FinancialDataClient; c = FinancialDataClient(); print(c.get_stock_info('NVDA'))"
   ```

3. **End-to-end test:**
   - Run `python app.py`
   - Query: "Analyze NVIDIA's current market position and recent news"
   - Verify report includes Western sources and financial data

---

## Implementation Order

1. **Phase 1** - Core improvements (1-2 days)
   - Fix 503 retry logic
   - Add basic caching

2. **Phase 1.5** - Prompt customization (1-2 days)
   - Update all prompts for Trade & Investment focus
   - Add financial terminology reference

3. **Phase 2** - Western integrations (3-5 days)
   - Reddit API (PRAW - official free tier)
   - Yahoo Finance (yfinance - free)
   - Twitter Scraper (twikit - free, requires account)
   - News Extractor (newspaper4k + Tavily)

4. **Phase 3** - Configuration (1 day)
   - Update .env and config.py
   - Update prompts for investment focus

5. **Phase 4** - Future (deferred)
   - Automated monitoring
