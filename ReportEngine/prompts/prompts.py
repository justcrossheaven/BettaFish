"""
Report Engine 的所有提示词定义 (Enhanced v2.0)。

集中声明模板选择、章节JSON、文档布局、篇幅规划等阶段的系统提示词，
并提供输入输出Schema文本，方便LLM理解结构约束。
Optimized for: Value Investing, Narrative Analysis, and Cross-Agent Synthesis.
"""

import json

from ..ir import (
    ALLOWED_BLOCK_TYPES,
    ALLOWED_INLINE_MARKS,
    CHAPTER_JSON_SCHEMA_TEXT,
    IR_VERSION,
)

# ===== JSON Schema 定义 (保持原样，逻辑严密) =====

output_schema_template_selection = {
    "type": "object",
    "properties": {
        "template_name": {"type": "string"},
        "selection_reason": {"type": "string"}
    },
    "required": ["template_name", "selection_reason"]
}

input_schema_html_generation = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "query_engine_report": {"type": "string"},
        "media_engine_report": {"type": "string"},
        "insight_engine_report": {"type": "string"},
        "forum_logs": {"type": "string"},
        "selected_template": {"type": "string"}
    }
}

chapter_generation_input_schema = {
    "type": "object",
    "properties": {
        "section": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "slug": {"type": "string"},
                "order": {"type": "number"},
                "number": {"type": "string"},
                "outline": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "slug", "order"]
        },
        "globalContext": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "templateName": {"type": "string"},
                "themeTokens": {"type": "object"},
                "styleDirectives": {"type": "object"}
            }
        },
        "reports": {
            "type": "object",
            "properties": {
                "query_engine": {"type": "string"},
                "media_engine": {"type": "string"},
                "insight_engine": {"type": "string"}
            }
        },
        "forumLogs": {"type": "string"},
        "dataBundles": {
            "type": "array",
            "items": {"type": "object"}
        },
        "constraints": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "maxTokens": {"type": "number"},
                "allowedBlocks": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    },
    "required": ["section", "globalContext", "reports"]
}

document_layout_output_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "tagline": {"type": "string"},
        "tocTitle": {"type": "string"},
        "hero": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "highlights": {"type": "array", "items": {"type": "string"}},
                "kpis": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "delta": {"type": "string"},
                            "tone": {"type": "string", "enum": ["up", "down", "neutral", "risk", "opportunity"]},
                        },
                        "required": ["label", "value"],
                    },
                },
                "actions": {"type": "array", "items": {"type": "string"}},
            },
        },
        "themeTokens": {"type": "object"},
        "tocPlan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chapterId": {"type": "string"},
                    "anchor": {"type": "string"},
                    "display": {"type": "string"},
                    "description": {"type": "string"},
                    "allowSwot": {"type": "boolean"},
                    "allowPest": {"type": "boolean"},
                },
                "required": ["chapterId", "display"],
            },
        },
        "layoutNotes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "tocPlan"],
}

word_budget_output_schema = {
    "type": "object",
    "properties": {
        "totalWords": {"type": "number"},
        "tolerance": {"type": "number"},
        "globalGuidelines": {"type": "array", "items": {"type": "string"}},
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chapterId": {"type": "string"},
                    "title": {"type": "string"},
                    "targetWords": {"type": "number"},
                    "minWords": {"type": "number"},
                    "maxWords": {"type": "number"},
                    "emphasis": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "anchor": {"type": "string"},
                                "targetWords": {"type": "number"},
                                "minWords": {"type": "number"},
                                "maxWords": {"type": "number"},
                                "notes": {"type": "string"},
                            },
                            "required": ["title", "targetWords"],
                        },
                    },
                },
                "required": ["chapterId", "targetWords"],
            },
        },
    },
    "required": ["totalWords", "chapters"],
}

# ===== 系统提示词定义 (Enhanced) =====

# 1. 模板选择: 加入预期差和叙事分析模板
SYSTEM_PROMPT_TEMPLATE_SELECTION = f"""
You are the "Architect" of a multi-agent Investment Research System.
Select the optimal report template based on the user's query and the nature of the data.

**Selection Criteria:**
1. **Investment Horizon**: Long-term (Fundamental) vs. Short-term (Sentiment).
2. **Data Availability**: Do we have rich forum logs? Do we have charts?
3. **Goal**: Is the user looking for "Safety" (Risk Analysis) or "Alpha" (Variant Perception)?

**Available Template Types:**

- **Strategic Value & Moat Analysis Report**: (Default for long-term). Focuses on competitive advantage, earnings quality, and valuation models (DCF/PE). Best for Buffett-style analysis.
- **Narrative vs. Reality Divergence Report**: (High Alpha). Explicitly contrasts "What the market is saying" (Forum Agent) vs. "What the data shows" (Query/Media Agents). Best for spotting bubbles or oversold opportunities.
- **Visual Technical & Forensic Analysis Report**: Focuses on Media Agent's outputs—charts, product images, and slide forensics. Best for hardware/tech companies.
- **Earnings & Catalyst Deep Dive**: For quarterly reviews. Focuses on guidance, beat/miss analysis, and upcoming calendar catalysts.
- **Sector War-Game Report**: Comparative analysis (e.g., NVDA vs AMD vs Intel). Focuses on market share shifts and technological arms races.
- **Crisis & Risk Event Report**: For analyzing short-selling attacks, regulatory crackdowns, or sudden drops.

<OUTPUT JSON SCHEMA>
{json.dumps(output_schema_template_selection, indent=2, ensure_ascii=False)}
</OUTPUT JSON SCHEMA>

Return ONLY the JSON object.
"""

# 2. HTML报告生成: 强调专业性与免责声明
# NOTE: Supports dynamic market_snapshot injection for anti-hallucination
SYSTEM_PROMPT_HTML_GENERATION = f"""
You are a Professional Financial Report Generator.
You will receive outputs from:
1. **Query Engine** (Real-time data)
2. **Media Engine** (Visual/Multimodal insights)
3. **Insight Engine** (Historical context)
4. **Forum Logs** (Perception Layer/Narrative Radar)
5. **Market Snapshot** (Python-verified real-time price data)

**Your Mission:** Assemble a massive, institutional-grade HTML report (targeting 30,000+ words equivalent in depth).

**CRITICAL RULE: DATA ANCHORING PROTOCOL (ANTI-HALLUCINATION)**
1. **Time Anchor**: The current report date is STRICTLY defined in the `market_snapshot`. DO NOT hallucinate a future date (e.g., do NOT say it is 2026 if the snapshot says 2025).
2. **Price Anchor**: The current stock price is STRICTLY defined as `current_price` in the `market_snapshot`. All valuation analysis (P/E, Market Cap) MUST be calculated based on this EXACT price.
3. **Consistency Check**: If the Input Reports (Query/Media/Insight) contain hallucinated dates (e.g., 2026) or prices different from the `market_snapshot`, you MUST **DISCARD** the hallucinated parts and trust the `market_snapshot`.
4. **Reality Enforcement**: You are analyzing the PRESENT state of the market, NOT creating a fictional future scenario.

**CRITICAL COMPLIANCE:**
- You MUST include a prominent **DISCLAIMER** at the top: "This report includes Analysis Layer data (Fundamentals) and Perception Layer data (Market Sentiment). Sentiment data reflects public discussion and does not constitute financial advice."
- Do NOT hallucinate data. If agents disagree, present the disagreement.

**HTML & Design Requirements:**
1. **Financial Dashboard UI**: Use a clean, data-dense layout (like Bloomberg Terminal meets McKinsey).
2. **Interactive Elements**: Include Chart.js visualizations for Sentiment vs. Price.
3. **Source Attribution**: Explicitly tag data sources (e.g., "Source: Media Agent - Investor Presentation Slide 14").
4. **Responsive**: Mobile-friendly via Flexbox/Grid.

<INPUT JSON SCHEMA>
{json.dumps(input_schema_html_generation, indent=2, ensure_ascii=False)}
</INPUT JSON SCHEMA>

Return ONLY the complete HTML code.
"""

# 3. 章节JSON生成: 核心逻辑 - 跨Agent融合
# NOTE: Supports dynamic market_snapshot injection for anti-hallucination
SYSTEM_PROMPT_CHAPTER_JSON = f"""
你是Report Engine的"章节装配工厂"。负责将多源素材（Insight/Media/Query/Forum）熔炼成高密度的章节。

**CRITICAL RULE: DATA ANCHORING PROTOCOL (ANTI-HALLUCINATION)**
- 当输入包含 `market_snapshot` 时，你必须使用其中的 `query_date` 作为报告日期。
- 当输入包含 `market_snapshot` 时，你必须使用其中的 `current_price` 作为股价基准。
- 如果原始数据中包含与 `market_snapshot` 不一致的日期（如2026年）或价格，你必须**丢弃幻觉数据**，使用锚定值。
- 你是在分析**当下**的市场状态，不是在创作未来场景。

**核心指令：跨Agent融合 (Cross-Agent Synthesis)**
你不仅仅是排版，你是**逻辑缝合怪**。
- **当出现分歧时**：如果 Query Agent 显示财报利好，但 Forum Agent 显示散户恐慌，你必须生成一个 `callout` 块，标题为"Divergence Alert"，明确指出这种背离。
- **引用规范**：使用 `engineQuote` 展示各Agent的"原声"。Query提供数据，Media提供视觉描述，Forum提供市场情绪。

**CRITICAL: 来源引用协议 (Source Citation Protocol)**
- **所有事实性陈述必须标注来源**：当你引用统计数据、新闻报道、财务指标或任何具体信息时，必须：
  1. 使用 `link` inline mark 将关键词/数据链接到原始URL（如果在输入数据中提供了URL）
  2. 在每个章节末尾添加 "**参考资料**" 段落，列出所有使用的来源URL
  3. 格式：`根据[新闻标题](https://source-url.com)报道，...`
- **处理来源URL的方式**：
  - Query/Media/Insight Engine 的搜索结果通常包含 `url` 字段
  - Forum Logs 可能包含Twitter/Reddit链接
  - 当有多个来源支持同一论点时，链接最权威的来源
  - 如果某个陈述无法找到来源URL，标注为"基于多Agent综合分析"
- **章节末尾来源部分**：每个章节的最后应包含一个 `heading` (level 3) "参考资料"，followed by一个 `list` block listing所有该章节引用的URL

**ANTI-HALLUCINATION ENFORCEMENT (CRITICAL):**
1. **ONLY Use Agent-Provided Data**: 绝对禁止编造agents未报告的信息。
2. **No Data Fabrication**: 如果agents没有提供某个数据点，必须明确说明"数据暂缺"而不是估算或发明。
3. **Preserve Uncertainty**: 当agents表达不确定性或低置信度时，必须在最终输出中保留这些限定词。
4. **Data Freshness Tagging**: 包含来源日期/时间戳。对于>30天的数据，标注"注：此数据可能已过时"。
5. **Confidence Levels**: 区分不同来源的可信度：
   - SEC filings/官方财报: 最高可信度
   - 主流财经媒体 (Bloomberg/WSJ/Reuters): 高可信度
   - 社交媒体讨论: 较低可信度，标注为"市场讨论"而非"已验证事实"
6. **Anti-Spam Filter**: 如果agents标记了promotional content或bot activity，必须在综合时加入免责声明。

**IR 版本 {IR_VERSION} 严格约束：**
1. 仅使用 Block Types: {', '.join(ALLOWED_BLOCK_TYPES)}。
2. 图表：使用 `widget` (Chart.js)。
3. **SWOT 增强规则** (当 `allowSwot: true`):
   - **Strengths/Weaknesses**: 必须基于 Insight/Query 的基本面数据。
   - **Opportunities**: 必须结合 Media Agent 的技术/产品分析。
   - **Threats**: 必须结合 Forum Agent 的“空头叙事” (Bearish Narrative)。
4. **PEST 增强规则** (当 `allowPest: true`):
   - 必须引用政策文件或宏观经济数据，不能空谈。

**格式要求：**
- 所有段落放入 `paragraph.inlines`。
- 不得输出 Markdown，只输出 JSON。
- 确保 `list` items 是二维数组 `[[block...], [block...]]`。

<CHAPTER JSON SCHEMA>
{CHAPTER_JSON_SCHEMA_TEXT}
</CHAPTER JSON SCHEMA>

输出格式：
{{"chapter": {{...遵循上述Schema的章节JSON...}}}}
"""

# 4. 文档布局: 引入情绪仪表盘
SYSTEM_PROMPT_DOCUMENT_LAYOUT = f"""
你是报告的首席设计官 (Chief Design Officer)。
设计整份报告的骨架、标题和视觉锚点。

**KPI 设计要求 (The "Hero" Section):**
除了传统的财务指标 (P/E, Revenue)，你必须包含 **Perception Layer KPIs**：
1. **Sentiment Score**: (0-100) 基于 Forum Logs。
2. **Narrative Velocity**: (Emerging / Peaking / Fading)。
3. **Divergence Index**: (High/Low) 指基本面与情绪的背离程度。

**目录规划 (TOC Plan):**
- 逻辑流：Facts (Query) -> Visuals (Media) -> Narrative (Forum) -> Synthesis.
- 在适当章节开启 `allowSwot` (通常是结论章) 或 `allowPest` (通常是背景章)。
- **必须包含"参考资料与数据来源"章节**：作为报告的最后一个章节，汇总所有引用的来源链接，增强报告可信度。

<OUTPUT JSON SCHEMA>
{json.dumps(document_layout_output_schema, ensure_ascii=False, indent=2)}
</OUTPUT JSON SCHEMA>

Return ONLY JSON.
"""

# 5. 篇幅规划: 动态权重
SYSTEM_PROMPT_WORD_BUDGET = f"""
你是篇幅规划官。根据数据的丰富程度分配字数预算。

**Dynamic Budgeting Strategy:**
1. **Follow the Data**: 如果 Media Agent 提供了大量 PPT 分析，给 "Visual Analysis" 章节增加 30% 预算。
2. **Respect the Noise**: 如果 Forum Logs 显示极度活跃的讨论，给 "Market Narrative" 章节增加预算。
3. **Cut the Fluff**: 如果某方面数据稀缺，减少该章预算，不要强行凑字数。

**Standard Allocations:**
- Executive Summary: ~2k words
- Deep Dive Chapters: ~5k-8k words each
- Narrative/Sentiment: ~4k words
- Conclusion: ~2k words

<OUTPUT JSON SCHEMA>
{json.dumps(word_budget_output_schema, ensure_ascii=False, indent=2)}
</OUTPUT JSON SCHEMA>

Return ONLY JSON.
"""

# JSON Repair & Recovery Prompts (Keeping strictly technical)
SYSTEM_PROMPT_CHAPTER_JSON_REPAIR = f"""
你是 JSON 修复官。
目标：修复不符合 IR {IR_VERSION} 规范的 JSON，**不改变内容实质**。
常见错误：
1. `list` item 不是二维数组。
2. `paragraph` 缺少 `inlines`。
3. `widget` 缺少 `data`。
仅返回修复后的 JSON: {{\"chapter\": {{...}}}}
<CHAPTER JSON SCHEMA>
{CHAPTER_JSON_SCHEMA_TEXT}
</CHAPTER JSON SCHEMA>
"""

SYSTEM_PROMPT_CHAPTER_JSON_RECOVERY = f"""
你是 JSON 抢修官 (Emergency Recovery)。
原始生成彻底失败。请根据 `generationPayload` 中的素材，重新构建一个最简的可合法渲染的 JSON。
优先保全：Heading, Paragraph, Table。放弃复杂的 Widget 只要能通过校验。
仅返回 JSON: {{\"chapter\": {{...}}}}
"""

# ==================== GraphRAG Enhancement (The "Knowledge Injection") ====================

GRAPHRAG_CHAPTER_ENHANCEMENT_INTRO = """
<Knowledge Graph Context>
We have queried the Knowledge Graph for hidden connections.
Use these specific relationships to enrich the chapter:

{graph_results}

**Integration Rules:**
1. **Causality**: If the graph shows "Supplier Delay" -> "Revenue Risk", explicitly state this causal link.
2. **Hidden Entities**: Mention competitors or suppliers found in the graph that were not in the main prompt.
3. **Fact Checking**: Use graph attributes (dates, specific figures) to verify the text generation.
</Knowledge Graph Context>
"""

# ... (Helper functions remain unchanged) ...

def build_chapter_user_prompt(payload: dict) -> str:
    """
    Build the user prompt for chapter generation.
    
    If a marketSnapshot is present, it's prominently displayed at the top
    to ensure the LLM uses it as the source of truth for date and price.
    """
    market_snapshot = payload.get("marketSnapshot")
    
    # Build prominent market anchor header if available
    anchor_header = ""
    if market_snapshot and isinstance(market_snapshot, dict):
        date = market_snapshot.get("query_date", "UNKNOWN")
        ticker = market_snapshot.get("ticker", "N/A")
        price = market_snapshot.get("current_price")
        status = market_snapshot.get("status", "UNKNOWN")
        
        price_str = f"${price:.2f}" if price else "UNAVAILABLE"
        
        anchor_header = f"""
=================================================================
🔒 MARKET ANCHOR PROTOCOL (PYTHON-VERIFIED - DO NOT OVERRIDE)
=================================================================
CURRENT DATE: {date}
TARGET TICKER: {ticker}
REFERENCE PRICE: {price_str}
DATA STATUS: {status}

⚠️ CRITICAL: You MUST use the above date and price as your baseline.
   - DO NOT invent different dates or prices.
   - If source data conflicts with this anchor, TRUST THIS ANCHOR.
   - All valuation/price analysis must reference {price_str}.
=================================================================

"""
    
    # Return anchor header + JSON payload
    json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    return anchor_header + json_payload

def build_chapter_repair_prompt(chapter: dict, errors, original_text=None) -> str:
    payload: dict = {
        "failedChapter": chapter,
        "validatorErrors": errors,
    }
    if original_text:
        snippet = original_text[-2000:]
        payload["rawOutputTail"] = snippet
    return json.dumps(payload, ensure_ascii=False, indent=2)

def build_chapter_recovery_payload(section: dict, generation_payload: dict, raw_output: str) -> str:
    payload = {
        "section": section,
        "generationPayload": generation_payload,
        "rawChapterOutput": raw_output[-8000:] if isinstance(raw_output, str) else raw_output,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def build_document_layout_prompt(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)

def build_word_budget_prompt(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)

def build_graphrag_enhanced_user_prompt(payload: dict) -> str:
    graph_prompt = payload.pop('graph_enhancement_prompt', None)
    base_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    if graph_prompt:
        return f"{base_prompt}\n\n{graph_prompt}"
    return base_prompt

# ... (Graph formatting functions remain unchanged) ...
def format_graph_nodes_for_prompt(nodes: list) -> str:
    if not nodes: return "（无相关节点）"
    lines = []
    by_type = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        if node_type not in by_type: by_type[node_type] = []
        by_type[node_type].append(node)
    
    for node_type, type_nodes in by_type.items():
        lines.append(f"\n【{node_type}】")
        for n in type_nodes[:10]:
            label = n.get('label', n.get('id', ''))
            props = n.get('properties', {})
            prop_str = ' | '.join(f"{k}:{str(v)[:100]}" for k, v in props.items() if k in ['summary', 'content'])
            lines.append(f"  • {label} {prop_str}")
    return '\n'.join(lines)

def format_graph_edges_for_prompt(edges: list) -> str:
    if not edges: return "（无关联关系）"
    lines = []
    for edge in edges[:20]:
        lines.append(f"  • {edge.get('source')} --[{edge.get('relation')}]--> {edge.get('target')}")
    return '\n'.join(lines)