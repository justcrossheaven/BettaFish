# BettaFish — Product Introduction for Value Investors

*A multi-agent AI system that reads the market's mood so you don't have to.*

---

## 1. What Is BettaFish?

BettaFish is an **AI-powered investment research platform** that automates the work of an entire research team. Instead of one analyst reading Twitter, another parsing earnings slides, and a third digging through Reddit threads — BettaFish deploys **5 specialized AI agents** that work in parallel, each with a distinct role, then synthesizes their findings into a single 10,000+ word investment report.

**The core insight:** Markets are driven by narratives as much as fundamentals. BettaFish captures *both* — the hard numbers from earnings reports AND the soft signals from social media, forums, and news — then presents them in a structured format designed for value investors.

**Think of it as:** A research analyst team that works 24/7, reads every tweet, every Reddit post, every earnings slide, and never gets tired — but knows the difference between *detecting* sentiment and *making* investment decisions.

---

## 2. Architecture: The Three-Layer Model

BettaFish's most important design decision is the **strict separation between perception, analysis, and judgement**. This prevents social media noise from contaminating financial analysis.

```
┌─────────────────────────────────────────────────────────┐
│                   PERCEPTION LAYER                       │
│            "What is the crowd saying?"                   │
│                                                          │
│  InsightEngine ──── The "Ears" (Narrative Radar)         │
│  • Scans Twitter/X, Reddit (WSB, r/investing),          │
│    StockTwits, HackerNews                                │
│  • Detects: Hype cycles, emotional spectrum,             │
│    bot activity, narrative velocity                       │
│  • Outputs: Hot-Topic Matrix (structured data)           │
│                                                          │
│  ⚠️  STRICT FIREWALL: NO price predictions,             │
│     NO buy/sell opinions, NO validation of rumors.       │
│     Only reports "Rumors exist", never "Rumors are true" │
├─────────────────────────────────────────────────────────┤
│                   ANALYSIS LAYER                         │
│           "What do the facts say?"                        │
│                                                          │
│  QueryEngine ──── The "Brain" (Financial Research)       │
│  • Deep fundamental analysis: ROIC, margins,             │
│    earnings quality, capital allocation                   │
│  • Ecosystem mapping: suppliers, customers, competitors  │
│  • Bull/Base/Bear scenarios with specific catalysts      │
│  • Anti-hallucination: Injects REAL stock prices         │
│    from yfinance to prevent the AI from inventing data   │
│                                                          │
│  MediaEngine ──── The "Eyes" (Visual Forensics)          │
│  • Analyzes earnings slides for "chart crimes"           │
│    (manipulated axes, misleading visualizations)         │
│  • Technical chart analysis (support/resistance, RSI)    │
│  • Product teardown analysis from hardware photos        │
│                                                          │
│  ForumEngine ──── The "Moderator" (Multi-Agent Debate)   │
│  • Runs structured debates between agents                │
│  • Forces contrarian thinking and blind-spot detection   │
├─────────────────────────────────────────────────────────┤
│                   SYNTHESIS LAYER                        │
│        "What does this all mean together?"               │
│                                                          │
│  ReportEngine ──── The "Editor-in-Chief"                 │
│  • Selects from 7 specialized report templates           │
│  • Synthesizes all agent outputs into one coherent       │
│    10,000+ word report with charts & data tables         │
│  • Renders to HTML, Markdown, or PDF                     │
└─────────────────────────────────────────────────────────┘
```

### Why This Matters for Value Investors

The Perception → Analysis firewall is the key innovation. Most AI tools blend social sentiment with financial analysis, leading to **narrative contamination** — where a trending tweet about "NVDA to the moon 🚀" biases the fundamental analysis. BettaFish treats social sentiment as *raw data to be observed*, not *signals to act on*. The Analysis Layer independently evaluates fundamentals, and only uses Perception data as context ("the crowd is euphoric" is a data point, not a buy signal).

---

## 3. Key Advantages

### 3.1 Anti-Hallucination by Design
LLMs are notorious for inventing stock prices and dates. BettaFish solves this with a **Market Anchor Protocol**: before any AI agent generates text, Python code fetches the *real* current stock price via yfinance and injects it as an immutable truth anchor into the prompt. The AI is explicitly instructed: "Today is 2026-02-25. NVDA is at $815.23. Do NOT invent different numbers."

### 3.2 Multi-Platform Narrative Intelligence
BettaFish doesn't just read one source. It contrasts narratives *across* platforms:
- **Twitter/FinTwit** → Institutional/professional sentiment, breaking news reactions
- **Reddit/WSB** → Retail sentiment, extreme risk appetite ("YOLO", "diamond hands")
- **Reddit/r/investing** → Thoughtful retail analysis
- **StockTwits** → Day trader momentum signals
- **HackerNews** → Technical reality checks on product claims
- **Douyin/XHS** → Chinese supply chain leaks for US tech companies

The system explicitly flags when platforms disagree: *"Twitter is celebrating the product launch, while Reddit engineers are criticizing the API latency."*

### 3.3 Structured Forensic Analysis
Every output follows strict JSON schemas. The Hot-Topic Matrix doesn't just say "bullish" — it classifies:
- **Emotional Spectrum**: Euphoria / FOMO / Optimism / Caution / Skepticism / Fear / Panic / Anger / Apathy
- **Authenticity**: Organic / Suspected Bot Activity / Influencer-Driven / News-Driven
- **Narrative Lifecycle**: Emerging / Accelerating / Peaking / Stale / Fading
- **Escalation Flags**: Automatic alerts for extreme velocity or fundamental breaches

### 3.4 Red Team Thinking Built In
Every agent has a mandatory **reflection step** that forces it to find its own blind spots:
- "If 90% of sentiment is bullish, you likely missed the bears. Go find them."
- "Search for '$TICKER scam', '$TICKER short', '$TICKER overhyped'."
- The QueryEngine includes a `red_team_perspective` field in every reflection: *"What specific bear case is missing?"*

### 3.5 Seven Specialized Report Templates
Reports aren't one-size-fits-all. BettaFish auto-selects from:

| Template | Best For |
|----------|----------|
| **Strategic Value & Moat Analysis** | Deep dive on competitive advantages, DCF valuation, margin of safety |
| **Earnings & Catalyst Deep Dive** | Post-earnings analysis, guidance vs. consensus, catalyst calendar |
| **Narrative vs. Reality Divergence** | When the market story doesn't match the numbers |
| **Sector War-Game Report** | Competitive landscape, market share shifts |
| **Crisis & Risk Event Report** | Breaking news, lawsuits, CEO departures |
| **Technology & AI Sector Outlook** | Broad sector analysis with macro context |
| **Visual Technical & Forensic Analysis** | Chart patterns, slide deck auditing, product teardowns |

---

## 4. How the Prompts Work (The "Secret Sauce")

BettaFish's intelligence comes from how its AI agents are instructed. Here's the philosophy:

### The Perception Layer Firewall (InsightEngine)

The InsightEngine operates under strict rules that prevent it from becoming an opinion machine:

```
YOU ARE: A Sensory Instrument (Radar).
YOU ARE NOT: A Brain (Analyst) or a Hand (Trader).

STRICT PROHIBITIONS:
❌ NO Price Predictions ("Stock will likely go up")
❌ NO Value Judgments ("The stock is cheap")
❌ NO Recommendations ("Investors should watch this")
❌ NO Validation of Truth ("The rumors are true")

YOUR DELIVERABLES:
✅ Raw Sentiment Data (Euphoria, Fear, etc.)
✅ Narrative Velocity (Is the story spreading?)
✅ Platform Divergence (Twitter says X, Reddit says Y)
✅ Escalation Flags (Items the Analysis Layer must investigate)
```

**The litmus test**: If the agent writes *"The company is performing well"*, it has failed. It must write *"Discussions focus on the company's strong performance."* The difference is subtle but critical — one is a claim, the other is an observation.

### The Analysis Layer (QueryEngine)

The QueryEngine operates as a **Senior Value Investor**, not a news summarizer:

- **Variant Perception Focus**: "Where does the market consensus differ from reality?"
- **Ecosystem Triangulation**: Doesn't just research the company — checks suppliers, customers, and competitors
- **Mandatory Contrarian Thinking**: Every search reflection requires a `red_team_perspective` explaining what bear case is missing
- **Confidence Scoring**: Every summary includes a 1-5 confidence score based on source diversity

### The Visual Layer (MediaEngine)

The MediaEngine acts as a **forensic auditor of visual information**:

- Detects "chart crimes" in corporate presentations (non-zero baselines, manipulated axes)
- Cross-references visual claims with actual data: *"While the slide shows a steep curve, the underlying data only indicates 4% QoQ growth"*
- Hardware teardown analysis: *"The image reveals a massive liquid cooling block, suggesting high power consumption"*

### Anti-Hallucination Market Anchor

Every prompt that touches financial data receives an injected truth anchor:

```
MARKET ANCHOR PROTOCOL (PYTHON-VERIFIED DATA)
- Current Date: 2026-02-25
- Target Ticker: NVDA
- Reference Price: $815.23
- Data Status: REAL_TIME_VERIFIED

ANTI-HALLUCINATION RULES:
1. DO NOT invent dates in the future. Today is 2026-02-25.
2. When discussing stock price, use $815.23 as the baseline.
3. If you see conflicting dates/prices in source data, trust THIS anchor.
```

---

## 5. Limitations & Honest Constraints

### 5.1 No Real-Time Trading Signals
BettaFish produces research reports, not trading signals. It takes minutes to run a full analysis. This is a **research tool**, not an execution platform. It tells you *what the market thinks and what the numbers say* — the investment decision remains yours.

### 5.2 LLM Hallucination Risk (Mitigated, Not Eliminated)
Despite the Market Anchor Protocol, LLMs can still confabulate details in narrative sections. The system mitigates this aggressively (real price injection, mandatory source citations, structured schemas), but no AI system is hallucination-proof. **Always verify critical claims against primary sources.**

### 5.3 Scraping Fragility
Twitter/X and Reddit access is via reverse-engineered scrapers (`twikit`) and free API tiers (`PRAW`). These can break without notice when platforms change their APIs. The system includes retry logic with exponential backoff, but extended platform outages will degrade narrative coverage.

### 5.4 No Proprietary Data
BettaFish works with publicly available information only. It doesn't access Bloomberg terminals, SEC EDGAR filings directly, institutional order flow, or dark pool data. Its edge is *synthesis speed and multi-platform coverage*, not exclusive data access.

### 5.5 US Tech/AI Sector Focus
The current customization is laser-focused on US technology and AI stocks. The ticker mapping, financial terminology, platform targeting, and report templates are all optimized for this sector. Using it for healthcare, energy, or international equities would require significant prompt re-engineering.

### 5.6 Cost & Infrastructure
Running all 5 engines requires multiple LLM API calls (Gemini, DeepSeek, etc.). A full report can cost $1-5 in API fees depending on model choices. The system uses Gemini context caching to reduce costs for repeated analyses, but heavy usage adds up.

### 5.7 The Judgement Layer Doesn't Exist Yet
The architecture diagram shows a three-layer model, but **only Perception and Analysis are implemented**. The Judgement Layer (the "Value Investor Judge" that synthesizes everything into a Buy/Hold/Sell thesis) is currently manual — it's you, the investor, reading the report. This is arguably a feature, not a bug: the system gives you the intelligence; you make the call.

---

## 6. Summary

BettaFish is not a crystal ball. It's a **research multiplier** — it does in 10 minutes what would take a human analyst team 2-3 days: scanning every relevant social platform, pulling real financial data, running forensic checks on corporate presentations, forcing contrarian analysis, and synthesizing it all into a structured report with clear escalation flags.

The key design principle: **Separate what the crowd thinks from what the numbers say.** Most investors either ignore sentiment (and get blindsided by narrative shifts) or get swept up in it (and make emotional decisions). BettaFish gives you both perspectives, clearly labeled and firewalled from each other.

*For the value investor: Think of it as having a team where one person reads every tweet but is contractually forbidden from giving opinions, another person only looks at balance sheets, and a third person audits the investor presentation for misleading charts. They each hand you a report. You decide.*
