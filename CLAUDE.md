# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BettaFish ("微舆") is a multi-agent public opinion analysis system built with Python. It uses AI agents to analyze social media content across 30+ platforms, generating comprehensive research reports through collaborative agent workflows.

## Common Commands

### Environment Setup

```bash
# Activate the conda environment (required before running any commands)
conda activate bettafish

# Or use conda run for one-off commands
conda run -n bettafish python app.py
```

### Running the Application

```bash
# Start main application (Flask + all agents)
python app.py

# Start individual agents via Streamlit
streamlit run SingleEngineApp/query_engine_streamlit_app.py --server.port 8503
streamlit run SingleEngineApp/media_engine_streamlit_app.py --server.port 8502
streamlit run SingleEngineApp/insight_engine_streamlit_app.py --server.port 8501
```

### Docker

```bash
docker compose up -d
```

### Testing

```bash
# Run all tests with pytest (use conda run if not in activated env)
conda run -n bettafish python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_monitor.py -v

# Run retry helper and caching tests
python -m pytest tests/test_retry_helper.py tests/test_gemini_cache.py -v

# Alternative: run tests directly
python tests/run_tests.py
```

### MindSpider Crawler

```bash
cd MindSpider
python main.py --setup                              # Initialize database
python main.py --broad-topic                        # Extract hot topics
python main.py --complete --date 2024-01-20         # Full crawl workflow
python main.py --deep-sentiment --platforms xhs dy wb  # Deep crawl specific platforms
```

### Report Generation CLI

```bash
python report_engine_only.py                        # Generate from latest logs
python report_engine_only.py --query "topic"        # Specify topic
python report_engine_only.py --skip-pdf             # Skip PDF generation
python report_engine_only.py --graphrag-enabled true  # Enable GraphRAG

# Re-render reports
python regenerate_latest_html.py
python regenerate_latest_md.py
python regenerate_latest_pdf.py
```

### Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

## Architecture

### Multi-Agent System

The system uses four specialized agents that work in parallel and communicate through a "Forum" mechanism:

1. **QueryEngine** (`QueryEngine/`) - Web search agent for domestic/international news
2. **MediaEngine** (`MediaEngine/`) - Multimodal agent for video/image content analysis
3. **InsightEngine** (`InsightEngine/`) - Private database mining agent with sentiment analysis
4. **ReportEngine** (`ReportEngine/`) - Report generation agent with template-based rendering

### Agent Structure Pattern

Each engine follows a consistent structure:
- `agent.py` - Main agent logic and orchestration
- `llms/base.py` - Native Gemini LLM client with hybrid caching support
- `nodes/` - Processing nodes (search, formatting, summary)
- `tools/` - Agent-specific toolsets
- `state/state.py` - Agent state management
- `prompts/prompts.py` - Prompt templates
- `utils/config.py` - Configuration (inherits from root `.env`)

### LLM Client & Caching (`utils/`)

- `retry_helper.py` - Retry logic with jitter for 503 "model overloaded" handling
- `gemini_cache_manager.py` - Hybrid context caching for Gemini API

**Caching Behavior:**
- **Implicit caching** (automatic, free): Used for system prompts (<2,048 tokens)
- **Explicit caching** (reduced cost): Used for large content (>10,000 chars / ~2,500 tokens)

Explicit caching activates when passing `context_content` parameter with large documents:
```python
client.invoke(
    system_prompt="You are a value investor...",
    user_prompt="Analyze NVIDIA's FCF",
    context_content=large_10k_report  # >10k chars triggers explicit cache
)
```

### ForumEngine (`ForumEngine/`)

Manages inter-agent communication through a moderator-driven debate mechanism:
- `monitor.py` - Log monitoring and forum management
- `llm_host.py` - LLM-powered forum moderator

### Report IR Pipeline

ReportEngine uses an Intermediate Representation (IR) for report generation:
1. Template selection → Document layout → Word budget → Chapter generation
2. IR validation (`ir/validator.py`, `ir/schema.py`)
3. Rendering to HTML/PDF/Markdown (`renderers/`)

### Data Flow

1. User query → Flask app (`app.py`)
2. Three agents (Query, Media, Insight) start parallel analysis
3. ForumEngine monitors and synthesizes agent outputs
4. ReportEngine collects results and generates IR
5. IR rendered to interactive HTML report

## Configuration

All configuration is managed through `.env` file (copy from `.env.example`). Key settings:

- **Database**: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_DIALECT` (postgresql/mysql)
- **LLM per agent**: `{AGENT}_API_KEY`, `{AGENT}_BASE_URL`, `{AGENT}_MODEL_NAME` where AGENT is INSIGHT_ENGINE, MEDIA_ENGINE, QUERY_ENGINE, REPORT_ENGINE, FORUM_HOST, KEYWORD_OPTIMIZER, MINDSPIDER
- **Search**: `SEARCH_TOOL_TYPE` (AnspireAPI/BochaAPI), `ANSPIRE_API_KEY`, `BOCHA_WEB_SEARCH_API_KEY`
- **GraphRAG**: `GRAPHRAG_ENABLED`, `GRAPHRAG_MAX_QUERIES`

All LLM calls use OpenAI-compatible API format.

## Key Directories

- `logs/` - Runtime logs including `forum.log` for agent communication
- `final_reports/` - Generated HTML reports and IR JSON files
- `*_engine_streamlit_reports/` - Individual agent output directories
- `SentimentAnalysisModel/` - Fine-tuned sentiment models (BERT, GPT-2, Qwen)
- `MindSpider/` - Social media crawler system with platform-specific implementations
- `ReportEngine/report_template/` - Markdown report templates (auto-selected by agent)

## Development Notes

- Flask runs on port 5000 by default; Streamlit apps on 8501-8503
- Database schema auto-initializes on first `app.py` run
- PDF export requires WeasyPrint system dependencies (see `static/Partial README for PDF Exporting/`)
- Agent logs write to both files and Socket.IO for real-time frontend updates

### Retry Configuration (LLM API Calls)

All LLM calls use `LLM_RETRY_CONFIG` from `utils/retry_helper.py`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| max_retries | 8 | Maximum retry attempts |
| initial_delay | 20s | Initial wait before first retry |
| backoff_factor | 1.8 | Exponential backoff multiplier |
| max_delay | 300s | Maximum delay between retries |
| jitter | True | Random ±30% variance to prevent thundering herd |

503 "model overloaded" errors are automatically detected and logged.

### Phase 1 Customization (Trade & Investment Focus)

The LLM clients have been updated from OpenAI-compatible wrappers to native Gemini SDK:
- `InsightEngine/llms/base.py` - Native Gemini with caching
- `QueryEngine/llms/base.py` - Native Gemini with caching  
- `MediaEngine/llms/base.py` - Native Gemini with caching

Log messages to watch for:
- `"Using implicit caching (standard request)"` - Normal operation
- `"Using explicit cached context"` - Large content being cached
- `"503 Model Overloaded detected"` - Retry triggered for overloaded API
