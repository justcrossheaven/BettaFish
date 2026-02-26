# BettaFish UI/CSS Improvements + Static Reports + Reference Links

## Summary of Changes

This document outlines the improvements made to the BettaFish project focusing on three key areas: UI/CSS modernization, static HTML report links, and reference link integration.

## 1. UI/CSS Improvements

### New Modern CSS (`static/css/modern.css`)
- **Design Philosophy**: Bloomberg Terminal meets clean SaaS aesthetic
- **Color Palette**: Dark theme with professional color scheme
  - Primary backgrounds: `#0a0e1a`, `#131825`, `#1a2030`
  - Accent colors: Blue (`#4a9eff`), Green (`#00d084`), Red (`#ff4757`), Yellow (`#ffa502`)
  - Improved text contrast and readability

### Key Features
- **Typography**: System fonts with fallbacks for cross-platform consistency
- **Spacing System**: Consistent spacing scale from xs (0.25rem) to xl (2rem)
- **Progress Indicators**: 
  - Smooth animated progress bars
  - Status badges (running, completed, error)
  - Indeterminate loading states
- **Toast Notifications**: 
  - Non-intrusive notifications
  - Auto-dismissing with smooth animations
  - Success, error, warning variants
- **Responsive Design**: Mobile-friendly breakpoints and flexbox layouts
- **Card Components**: Consistent card styling with headers and actions
- **Button System**: Primary, success, danger, and outline variants

## 2. Static HTML Report Links

### Changes Made

#### Backend (`ReportEngine/agent.py`)
```python
# Modified _save_report() method to:
# 1. Save reports to static/reports/ directory
# 2. Track both original and static paths
# 3. Return static_report_path for web access
```

**Key Implementation:**
- Reports are now saved to TWO locations:
  1. `final_reports/` (original location)
  2. `static/reports/` (web-accessible)
- Each report gets a unique filename: `final_report_{topic}_{timestamp}.html`
- The static path is tracked in `task.static_report_path`

#### Flask Interface (`ReportEngine/flask_interface.py`)
- Added `static_report_path` field to `ReportTask` class
- Updated `to_dict()` method to expose static path to API clients
- Report completion events now include the static URL

#### Frontend (`templates/index.html`)
- Modified `case 'completed'` handler to display clickable report links
- Format: `📄 报告已生成！点击查看: <a href="/static/reports/..." target="_blank">report_name.html</a>`
- Links open in new tab for better UX

### Usage
When a report is completed, users will see:
1. Success message in console
2. Clickable link to the static HTML report
3. Link opens in new browser tab

## 3. Reference Links for Facts

### Prompt Modifications (`ReportEngine/prompts/prompts.py`)

#### A. Source Citation Protocol
Added comprehensive instructions to `SYSTEM_PROMPT_CHAPTER_JSON`:

```
**CRITICAL: 来源引用协议 (Source Citation Protocol)**
- 所有事实性陈述必须标注来源
- 使用 `link` inline mark 链接到原始URL
- 每个章节末尾添加 "**参考资料**" 段落
- 格式：根据[新闻标题](https://source-url.com)报道，...
```

#### B. Chapter-Level References
Each chapter must include:
- Inline citations with hyperlinks
- References section at chapter end (level 3 heading)
- List of all sources used in that chapter

#### C. Global References Chapter
Updated `SYSTEM_PROMPT_DOCUMENT_LAYOUT` to require:
- A final chapter: "参考资料与数据来源"
- Aggregates all sources from all chapters
- Enhances report credibility

### Data Flow
1. **QueryEngine/InsightEngine/MediaEngine** → Search results include `url` field
2. **ReportEngine prompts** → Instruct LLM to use these URLs
3. **Chapter generation** → Links embedded as `{type: 'link', url: '...', text: '...'}`
4. **HTML Renderer** → Converts to clickable `<a>` tags

### Source Handling
- Prioritize authoritative sources when multiple sources support same claim
- Handle missing URLs gracefully: label as "基于多Agent综合分析"
- Forum logs (Twitter/Reddit) links also included when available

## File Changes Summary

### Modified Files
1. `ReportEngine/agent.py` - Static report saving
2. `ReportEngine/flask_interface.py` - API exposure of static paths
3. `ReportEngine/prompts/prompts.py` - Source citation instructions
4. `templates/index.html` - Clickable report links in UI

### New Files
1. `static/css/modern.css` - Modern UI stylesheet
2. `static/reports/` - Directory for web-accessible reports (auto-created)

## Testing

### Manual Testing Steps
1. **Start Flask app**: `python app.py`
2. **Generate report**: Use the UI to create a report
3. **Verify**:
   - Check console for completion message with link
   - Click the link → report opens in new tab
   - Verify report is in `static/reports/` directory
   - Check report content for inline citations (blue hyperlinks)
   - Scroll to end → verify "参考资料" sections exist

### Expected Behavior
- ✅ Reports saved to both `final_reports/` and `static/reports/`
- ✅ Clickable links appear in UI on completion
- ✅ Reports include inline source citations
- ✅ Each chapter has "References" section
- ✅ Final chapter lists all data sources

## Backward Compatibility

All changes are backward compatible:
- Original `final_reports/` directory still used
- Existing APIs unchanged (only additions)
- Old reports still accessible through download endpoint
- Static reports are additional, not replacement

## Future Enhancements

Potential improvements for next iteration:
1. **CSS Integration**: Link modern.css in `<head>` of index.html
2. **Toast System**: Implement JavaScript toast notifications for all events
3. **Source Validation**: Backend validation of URLs before rendering
4. **Citation Formatting**: Support different citation styles (APA, MLA, etc.)
5. **Source Metrics**: Track and display "source quality score"

## Technical Notes

### Why Static Directory?
- Flask automatically serves `static/` folder
- No additional routing needed
- CDN-friendly for future scaling
- Persistent across deployments

### URL Structure
```
http://localhost:5000/static/reports/final_report_{topic}_{timestamp}.html
```

### Prompt Engineering Insights
- LLMs need explicit formatting instructions for URLs
- JSON schema must support `link` inline mark type
- "CRITICAL" and "MUST" keywords increase compliance
- Examples in prompts improve citation quality

## Conclusion

These changes significantly improve:
1. **User Experience**: Modern, professional UI with clear feedback
2. **Accessibility**: Direct links to reports without navigation
3. **Credibility**: Proper source attribution builds trust
4. **Transparency**: Users can verify claims by checking sources

All changes follow best practices and maintain code quality standards.
