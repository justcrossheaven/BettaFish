"""
Forum Host Module - Narrative Radar Agent (Enhanced v2.0)
Uses LLM as forum host to guide multi-agent discussions for Trade & Investment analysis.
Focuses on market sentiment detection without providing investment recommendations.
"""

from openai import OpenAI
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import tiktoken  # Optional: for token counting if needed

# 添加项目根目录到Python路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# 添加utils目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(root_dir, 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

from utils.retry_helper import with_graceful_retry, SEARCH_API_RETRY_CONFIG


class ForumHost:
    """
    Forum Host - Narrative Radar Agent
    Scans and summarizes market narratives across multiple agents.
    IMPORTANT: This is a Perception Layer component - does NOT provide investment advice.
    """
    
    def __init__(self, api_key: str = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化论坛主持人
        """
        self.api_key = api_key or settings.FORUM_HOST_API_KEY
        if not self.api_key:
            raise ValueError("未找到论坛主持人API密钥，请在环境变量文件中设置FORUM_HOST_API_KEY")

        self.base_url = base_url or settings.FORUM_HOST_BASE_URL

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = model_name or settings.FORUM_HOST_MODEL_NAME 
        
        # Memory State: Keep track of the last summary to enable narrative evolution analysis
        self.last_host_summary = None
        self.max_history_turns = 15  # Sliding window: Only look at last 15 interactions

    def generate_host_speech(self, forum_logs: List[str]) -> Optional[str]:
        """
        生成主持人发言
        """
        try:
            # 1. Parse logs (Robust Method)
            parsed_content = self._parse_forum_logs(forum_logs)
            
            # 2. Check for silence
            if not parsed_content['agent_speeches']:
                print("ForumHost: 没有找到有效的agent发言")
                return None
            
            # 3. Apply Sliding Window (Context Management)
            recent_speeches = parsed_content['agent_speeches'][-self.max_history_turns:]
            parsed_content['agent_speeches'] = recent_speeches
            
            # 4. Build Prompts (Injecting Memory)
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(parsed_content, self.last_host_summary)
            
            # 5. Call LLM
            response = self._call_qwen_api(system_prompt, user_prompt)
            
            if response["success"]:
                speech = response["content"]
                # Clean up formatting
                speech = self._format_host_speech(speech)
                
                # Update Memory
                self.last_host_summary = speech
                
                return speech
            else:
                print(f"ForumHost: API调用失败 - {response.get('error', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"ForumHost: 生成发言时出错 - {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_forum_logs(self, forum_logs: List[str]) -> Dict[str, Any]:
        """
        解析论坛日志，提取agent发言 (增强版)
        """
        parsed = {
            'agent_speeches': []
        }
        
        # Enhanced regex to handle optional date parts: [2026-01-01 10:00:00] or [10:00:00]
        # And handle strictly defined speakers
        log_pattern = re.compile(r'\[(.*?)\]\s*\[(INSIGHT|MEDIA|QUERY|HOST|SYSTEM)\]\s*(.+)', re.DOTALL)

        for line in forum_logs:
            if not line.strip():
                continue
            
            match = log_pattern.match(line)
            if match:
                timestamp, speaker, content = match.groups()
                
                # Filter out system noise and self-talk
                if speaker in ['SYSTEM', 'HOST']:
                    continue
                
                # Unescape newlines if the logging system escaped them
                content = content.replace('\\n', '\n').strip()
                
                parsed['agent_speeches'].append({
                    'timestamp': timestamp,
                    'speaker': speaker,
                    'content': content
                })
        
        return parsed
    
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt (v2.0) - Integrating Hype Cycle & Authenticity Checks
        """
        return """You are the Narrative Radar Agent (Forum Host) for a multi-agent investment analysis system.

**CORE IDENTITY: The "Ears" of the System.**
- You operate in the Perception Layer.
- You listen to agents (INSIGHT, MEDIA, QUERY).
- You synthesize their findings into a "Market Pulse" report.

**STRICT FIREWALL (INSTANT FAIL CONDITIONS):**
1. ❌ NO Investment Advice (Buy/Sell/Hold).
2. ❌ NO Price Predictions ("Stock will go up").
3. ❌ NO Validation of Truth ("The rumors are true"). You only report that "Rumors exist".

**YOUR ANALYTICAL FRAMEWORK:**
1. **The Hype Cycle**: Identify if narratives are Emerging, Peaking, or Fading.
2. **Platform Divergence**: highlight if Twitter (Hype) disagrees with Analyst Reports (Data).
3. **Sentiment Spectrum**: Use precise emotions: "Euphoria", "Panic", "Skepticism", "Apathy".
4. **Blind Spot Detection**: If agents are only sharing bullish news, ask: "Where are the bears?"

**OUTPUT FORMAT:**
- Keep it under 800 words.
- Use bullet points.
- Structure: 
  1. Timeline & Events
  2. Narrative Dynamics (Hype Cycle & Emotion)
  3. Escalation Flags (Fundamental/Governance Risks)
  4. Questions for Agents (Guide the next turn)
"""
    
    def _build_user_prompt(self, parsed_content: Dict[str, Any], last_summary: str = None) -> str:
        """
        Build user prompt with MEMORY INJECTION
        """
        # 1. Format Speeches
        recent_speeches = parsed_content['agent_speeches']
        speeches_text = ""
        for s in recent_speeches:
            speeches_text += f"--- {s['speaker']} ({s['timestamp']}) ---\n{s['content']}\n\n"
        
        # 2. Inject Memory (Critical for continuity)
        memory_context = ""
        if last_summary:
            memory_context = f"""
**PREVIOUS CONTEXT (What you reported last time):**
To ensure continuity, here is your previous summary. 
Check if the narrative has shifted (e.g., from "Fear" to "Acceptance") since then.
{last_summary[-1000:]}  # Truncate to save tokens if needed
"""

        # 3. Construct Final Prompt
        prompt = f"""
**Current Agent Discussion Logs (Last {len(recent_speeches)} turns):**
{speeches_text}

{memory_context}

**MISSION:**
Synthesize the above discussion into a Narrative Radar Report.

**REQUIREMENTS:**
1. **Detect Changes**: Compare current discussions with the Previous Context. Is sentiment heating up or cooling down?
2. **Synthesize**: 
   - QUERY found: [Search Results]
   - MEDIA found: [Visual Evidence]
   - INSIGHT found: [Historical Data]
   -> **HOST Conclusion**: "While data is strong, the visual narrative suggests..."
3. **Escalate**: Flag specific items that touch **Fundamentals** or **Governance** for the Analysis Layer.

**Output Structure:**
I. Event Timeline (Chronological)
II. Narrative Dynamics (Emotion & Lifecycle)
III. Cross-Agent Synthesis (Consensus vs. Divergence)
IV. Escalation & Guidance (Next steps for agents)
"""
        return prompt
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return={"success": False, "error": "API服务暂时不可用"})
    def _call_qwen_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用Qwen API (Enhanced with Time injection)"""
        try:
            # 动态注入时间，确保时效性
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
            time_context = f"Current System Time: {current_time_str}\n"
            
            final_user_prompt = time_context + user_prompt
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": final_user_prompt}
                ],
                temperature=0.5, # Slightly lower temp for stability in hosting
                top_p=0.9,
            )

            if response.choices:
                content = response.choices[0].message.content
                return {"success": True, "content": content}
            else:
                return {"success": False, "error": "API返回格式异常"}
        except Exception as e:
            return {"success": False, "error": f"API调用异常: {str(e)}"}
    
    def _format_host_speech(self, speech: str) -> str:
        """格式化主持人发言"""
        speech = re.sub(r'\n{3,}', '\n\n', speech)
        speech = speech.strip('"\'""‘’')
        return speech.strip()


# 创建全局实例
_host_instance = None

def get_forum_host() -> ForumHost:
    """获取全局论坛主持人实例"""
    global _host_instance
    if _host_instance is None:
        _host_instance = ForumHost()
    return _host_instance

def generate_host_speech(forum_logs: List[str]) -> Optional[str]:
    """生成主持人发言的便捷函数"""
    return get_forum_host().generate_host_speech(forum_logs)