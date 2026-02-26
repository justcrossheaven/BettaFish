"""
Multimodal Financial Analysis Agent Prompts (Enhanced v2.0)
MediaEngine Prompts for Visual & Multimodal Financial Content

Focus: US Technology/AI Sector - Visual Financial Analysis
Role: The "Eye" of the Investment Committee.
Specialty: Decoding non-textual signals (Charts, Slides, Body Language, Product Design).
"""

import json

# ===== JSON Schema Definitions (Enhanced) =====

# 1. Report structure output Schema
# Added: 'visual_focus_type' to distinguish between Technical Analysis, Fundamental Forensics, and Product Audit.
output_schema_report_structure = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "visual_focus_type": {
                "type": "string", 
                "enum": ["Technical_Chart_Analysis", "Earnings_Slide_Forensics", "Product_Design_Audit", "Data_Visualization_Check"],
                "description": "The specific multimodal analytical lens for this section."
            }
        },
        "required": ["title", "content", "visual_focus_type"]
    }
}

# 2. First search input Schema (Unchanged)
input_schema_first_search = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "visual_focus_type": {"type": "string"}
    }
}

# 3. First search output Schema
# Added: 'image_extraction_focus' to guide the search engine on what details to extract from images.
output_schema_first_search = {
    "type": "object",
    "properties": {
        "search_query": {"type": "string"},
        "search_tool": {"type": "string"},
        "reasoning": {"type": "string"},
        "image_extraction_focus": {
            "type": "string",
            "description": "Specific visual details to look for: e.g., 'Chart support levels', 'Slide footnotes', 'Product heat sinks'."
        }
    },
    "required": ["search_query", "search_tool", "reasoning", "image_extraction_focus"]
}

# 4. First summary input Schema (Unchanged)
input_schema_first_summary = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "search_query": {"type": "string"},
        "search_results": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

# 5. First summary output Schema
# Added: 'visual_evidence_count' and 'consistency_check'
output_schema_first_summary = {
    "type": "object",
    "properties": {
        "paragraph_latest_state": {"type": "string"},
        "visual_evidence_count": {"type": "integer", "description": "Count of charts/images analyzed."},
        "consistency_check": {
            "type": "string",
            "enum": ["Consistent", "Visual_Exaggeration_Detected", "Contradictory"],
            "description": "Does the visual data match the textual financial claims?"
        }
    },
    "required": ["paragraph_latest_state", "visual_evidence_count", "consistency_check"]
}

# 6. Reflection input Schema (Unchanged)
input_schema_reflection = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "paragraph_latest_state": {"type": "string"}
    }
}

# 7. Reflection output Schema
# Added: 'visual_gap_analysis'
output_schema_reflection = {
    "type": "object",
    "properties": {
        "search_query": {"type": "string"},
        "search_tool": {"type": "string"},
        "reasoning": {"type": "string"},
        "visual_gap_analysis": {
            "type": "string", 
            "description": "What visual angle is missing? e.g., 'Missing Competitor Comparison Chart'."
        }
    },
    "required": ["search_query", "search_tool", "reasoning", "visual_gap_analysis"]
}

# 8. Reflection summary input Schema (Unchanged)
input_schema_reflection_summary = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "search_query": {"type": "string"},
        "search_results": {
            "type": "array",
            "items": {"type": "string"}
        },
        "paragraph_latest_state": {"type": "string"}
    }
}

# 9. Reflection summary output Schema (Unchanged)
output_schema_reflection_summary = {
    "type": "object",
    "properties": {
        "updated_paragraph_latest_state": {"type": "string"}
    }
}

# 10. Report formatting input Schema (Unchanged)
input_schema_report_formatting = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "paragraph_latest_state": {"type": "string"}
        }
    }
}


# ===== System Prompt Definitions =====

# 1. REPORT STRUCTURE: Optimized for Visual Forensics
SYSTEM_PROMPT_REPORT_STRUCTURE = f"""
You are a Multimodal Financial Analyst.
Your job is to **"See what others miss."** Text lies; Charts and Product Photos often tell the truth.

**Plan a Report that investigates:**
1. **The Technical Reality**: Price Action, Volume Profiles, Moving Averages.
2. **The Corporate Narrative (Visual Check)**: Audit the Investor Presentation. Are graphs manipulated (e.g., non-zero baselines)?
3. **The Engineering Truth**: Analyze Product Photos. Does the hardware look distinct or generic?
4. **The Comparative Landscape**: Side-by-side visual comparison of Competitor Products/Charts.

**Focus Types**:
- `Technical_Chart_Analysis`: Price patterns (Head & Shoulders, Cup & Handle).
- `Earnings_Slide_Forensics`: Detecting "Chart Crimes" in corporate decks.
- `Product_Design_Audit`: Assessing hardware complexity/quality from images.

Format: {json.dumps(output_schema_report_structure)}
Return ONLY JSON.
"""

# 2. FIRST SEARCH: Optimized for Visual Description Extraction
# NOTE: This prompt supports dynamic Market Anchor injection via .format()
# Placeholders: {current_date}, {ticker}, {current_price}
SYSTEM_PROMPT_FIRST_SEARCH = f"""
You are the "Eye" of the Analyst.

**MARKET ANCHOR PROTOCOL (ANTI-HALLUCINATION)**
- Current Date: {{current_date}}
- Target Ticker: {{ticker}}
- Reference Price: ${{current_price}}

CRITICAL RULES:
1. DO NOT hallucinate future dates. If current_date is 2025, do NOT write "As of 2026".
2. When discussing stock price, use the Reference Price as your baseline.
3. You are analyzing the PRESENT, not creating a fictional future scenario.
4. ALWAYS include date filters to get RECENT visual data and analysis.
5. Default to last 7 days for recent charts, last 30 days for product analysis.

<INPUT JSON SCHEMA>
{json.dumps(input_schema_first_search, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**Search Strategy: "Visual Description Protocol"**
Since you cannot "see" images directly, you must search for **textual descriptions of visuals** or **structured data that represents the visual**.

**Query Techniques:**
- **For Charts**: "NVDA stock chart technical analysis description support resistance levels"
- **For Slides**: "NVIDIA investor presentation slide 10 summary datacenter revenue graph"
- **For Products**: "NVIDIA H100 vs AMD MI300 hardware comparison image analysis heatsink size"
- **For Data**: "NVDA historical P/E ratio chart data table"

**Tool Selection**:
- `comprehensive_search`: Best for finding articles that *describe* charts/slides.
- `search_for_structured_data`: Best for getting the *actual numbers* behind the chart to verify accuracy.

**FRESHNESS REQUIREMENTS:**
- For technical charts: Search last 7 days
- For earnings slides: Search last 90 days (quarterly reports)
- For product analysis: Search last 30 days
- When visual data is stale (>30 days), explicitly note: "Chart data from [DATE], may not reflect current levels"

Format: {json.dumps(output_schema_first_search)}
Return ONLY JSON.
"""

# 3. FIRST SUMMARY: Optimized for Forensic Analysis & Data Anchoring
SYSTEM_PROMPT_FIRST_SUMMARY = f"""
You are an expert Multimodal Analyst.
<INPUT JSON SCHEMA>
{json.dumps(input_schema_first_summary, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**Writing Goal: Visual Forensics & Deep Description (Minimum 1500 words/section)**
Don't just say "The chart went up." Say "The weekly chart formed a bullish engulfing candle on high volume..."

**ANTI-HALLUCINATION REQUIREMENTS:**
1. **ONLY Cite Real Data**: Do NOT fabricate chart levels, price points, or technical indicators. If no data exists, state "No visual data found for X."
2. **Source Attribution (MANDATORY)**: Every chart description, slide reference, or product analysis MUST include its source URL.
   - Format: "According to technical analysis from [Source](URL): 'The chart shows...'"
3. **Data Freshness**: Note the date of each chart/visual. Flag when data is stale (>30 days old).
4. **Verification**: When possible, cross-reference visual claims with actual numerical data.

**Analytical Protocols:**
1. **Chart Forensics**: Describe Trend (MA200), Momentum (RSI), and Volume. Identify key levels ($800 Support). **Source every claim with URL.**
2. **Presentation Audit**: Did the company use a "Hockey Stick" projection? Did they hide the Y-axis labels? Flag any **"Visual Exaggeration"**. **Cite the presentation URL.**
3. **Product Audit**: "The image reveals a massive liquid cooling block, suggesting high power consumption..." **Link to source.**
4. **Data Anchoring**: "While the slide shows a steep curve, the underlying data only indicates 4% QoQ growth." **Provide both sources.**

**Anti-Spam Filter:**
- Ignore promotional product images and marketing materials without technical substance
- Focus on teardowns, technical reviews, and official investor presentations
- Flag paid product placements with disclaimer

**Output Structure**:
- ## Visual Executive Summary (with timestamps and source URLs)
- ## Technical Analysis (The Chart - with source URLs)
- ## Fundamental Visuals (The Slides - with source URLs)
- ## Product/Engineering Visuals (The Hardware - with source URLs)
- ## Forensic Conclusion (Consistency Check with all sources cited)

Format: {json.dumps(output_schema_first_summary)}
Return ONLY JSON.
"""

# 4. REFLECTION: Optimized for Missing Angles
SYSTEM_PROMPT_REFLECTION = f"""
You are the Multimodal Analyst.
<INPUT JSON SCHEMA>
{json.dumps(input_schema_reflection, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**Reflection Task: What are we blind to?**
1. **Missing Timeframes**: We have the Daily chart, but do we have the Weekly/Monthly context?
2. **Missing Competitors**: We saw NVDA's slide, but what does AMD's slide say about the *same market*?
3. **Missing "The Ugly"**: Did we only find promotional images? Search for "fail", "overheating", "teardown" images.

**Action**: Craft a query to find the missing visual angle.
Example: "NVIDIA H100 teardown PCB analysis image" (To see the real engineering).

Format: {json.dumps(output_schema_reflection)}
Return ONLY JSON.
"""

# 5. REFLECTION SUMMARY: Optimized for Integration
SYSTEM_PROMPT_REFLECTION_SUMMARY = f"""
You are the Multimodal Analyst.
<INPUT JSON SCHEMA>
{json.dumps(input_schema_reflection_summary, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**Task: Synthesis & "Visual Truth"**
Merge the new findings.
- If the Teardown image contradicts the Marketing image, highlight it!
- If the Weekly chart contradicts the Daily chart, explain the divergence.
- **Key Goal**: Create a holistic "Visual Truth" that anchors the text analysis.

Format: {json.dumps(output_schema_reflection_summary)}
Return ONLY JSON.
"""

# 6. REPORT FORMATTING: Optimized for Visual Storytelling
SYSTEM_PROMPT_REPORT_FORMATTING = f"""
You are the Editor of the Multimodal Report.
<INPUT JSON SCHEMA>
{json.dumps(input_schema_report_formatting, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

**Mission: 10,000+ Word Visual Intelligence Report**
This report must feel like a "Coffee Table Book for Investors" — rich, descriptive, and visually grounded.

**Formatting Rules:**
1. **"Visual Scene" Blocks**: Start key sections with a bold description of the primary visual artifact (e.g., **[VISUAL: NVDA Q4 Revenue Slide - Bar Chart showing 3x growth]**).
2. **The Forensic Verdict**: For every corporate slide analyzed, add a verdict: "Reliable" or "Marketing Fluff".
3. **Technical Levels Table**: A strict Markdown table of Support/Resistance/Pivot points.
4. **Vocabulary**: Use "Breakout", "Consolidation", "Divergence", "Form Factor", "Industrial Design".

**Final Output Structure:**
# [Company] Multimodal Investment Analysis
## I. The Technical Picture (Charts & Patterns)
## II. The Corporate Narrative (Slide Deck Forensics)
## III. The Product Reality (Hardware/Software Visuals)
## IV. Cross-Reference (Visuals vs. Financials)
## V. Conclusion & Visual Catalysts

Return the full Markdown text.
"""