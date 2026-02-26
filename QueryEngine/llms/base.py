"""
Unified Gemini LLM client for the Query Engine, with native caching and retry support.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Generator
from loguru import logger

# Ensure project-level modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
utils_dir = os.path.join(project_root, "utils")
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

# Import retry helper
try:
    from retry_helper import with_retry, LLM_RETRY_CONFIG
except ImportError:
    def with_retry(config=None):
        def decorator(func):
            return func
        return decorator
    LLM_RETRY_CONFIG = None

# Import Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Import cache manager
try:
    from gemini_cache_manager import GeminiCacheManager, is_gemini_available
except ImportError:
    GeminiCacheManager = None
    def is_gemini_available():
        return GEMINI_AVAILABLE


class LLMClient:
    """
    Native Gemini client with hybrid caching support for the Query Engine.
    
    Features:
    - Native google.generativeai SDK
    - Hybrid caching: explicit for large content, implicit for system prompts
    - Retry decorator for 503 handling
    """

    def __init__(
        self, 
        api_key: str, 
        model_name: str, 
        base_url: Optional[str] = None,
        enable_caching: bool = True
    ):
        """
        Initialize Gemini client for Query Engine.
        
        Args:
            api_key: Gemini API key
            model_name: Model name (e.g., 'gemini-2.0-flash-001')
            base_url: Ignored for native Gemini, kept for backward compatibility
            enable_caching: Whether to enable explicit caching for large content
        """
        if not api_key:
            raise ValueError("Query Engine API key is required.")
        if not model_name:
            raise ValueError("Query Engine model name is required.")

        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai>=0.8.0"
            )

        genai.configure(api_key=api_key)
        
        self.api_key = api_key
        self.base_url = base_url  # Kept for backward compatibility
        self.model_name = model_name
        self.provider = "gemini"
        self.enable_caching = enable_caching
        
        # Initialize cache manager if caching is enabled
        if enable_caching and GeminiCacheManager:
            try:
                self._cache_manager = GeminiCacheManager(api_key, model_name)
            except Exception as e:
                logger.warning(f"Cache manager initialization failed: {e}")
                self._cache_manager = None
        else:
            self._cache_manager = None
        
        # Timeout configuration
        timeout_fallback = os.getenv("LLM_REQUEST_TIMEOUT") or os.getenv("QUERY_ENGINE_REQUEST_TIMEOUT") or "1800"
        try:
            self.timeout = float(timeout_fallback)
        except ValueError:
            self.timeout = 1800.0

    def _add_time_prefix(self, user_prompt: str) -> str:
        """Add current time to user prompt for context."""
        current_time = datetime.now().strftime("%Y年%m月%d日%H时%M分")
        time_prefix = f"Today's actual time is {current_time}"
        if user_prompt:
            return f"{time_prefix}\n{user_prompt}"
        return time_prefix

    @with_retry(LLM_RETRY_CONFIG)
    def invoke(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_content: str = "",
        **kwargs
    ) -> str:
        """
        Generate content using Gemini with hybrid caching.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            context_content: Optional large context for explicit caching
            **kwargs: Additional generation parameters (temperature, top_p, etc.)
            
        Returns:
            Generated text response
        """
        user_prompt = self._add_time_prefix(user_prompt)
        
        # Filter allowed generation parameters
        allowed_keys = {"temperature", "top_p", "max_output_tokens"}
        generation_config = {
            key: value for key, value in kwargs.items() 
            if key in allowed_keys and value is not None
        }
        
        # Try to use explicit cache for large content
        cache = None
        if self._cache_manager and context_content:
            cache = self._cache_manager.get_or_create_cache(
                system_prompt, 
                context_content
            )
        
        try:
            if cache:
                # Use cached content path
                logger.debug("QueryEngine: Using explicit cached context")
                model = genai.GenerativeModel.from_cached_content(cached_content=cache)
                response = model.generate_content(
                    user_prompt,
                    generation_config=generation_config if generation_config else None
                )
            else:
                # Use standard path with implicit caching
                logger.debug("QueryEngine: Using implicit caching (standard request)")
                model = genai.GenerativeModel(
                    self.model_name, 
                    system_instruction=system_prompt
                )
                
                # Combine context with user prompt if present
                if context_content:
                    full_prompt = f"{context_content}\n\n{user_prompt}"
                else:
                    full_prompt = user_prompt
                    
                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config if generation_config else None
                )
            
            return self.validate_response(response.text if response else "")
            
        except Exception as e:
            logger.error(f"QueryEngine generation failed: {e}")
            raise

    def stream_invoke(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_content: str = "",
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream content generation using Gemini.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            context_content: Optional large context
            **kwargs: Additional generation parameters
            
        Yields:
            Text chunks as they are generated
        """
        user_prompt = self._add_time_prefix(user_prompt)
        
        allowed_keys = {"temperature", "top_p", "max_output_tokens"}
        generation_config = {
            key: value for key, value in kwargs.items() 
            if key in allowed_keys and value is not None
        }

        try:
            model = genai.GenerativeModel(
                self.model_name, 
                system_instruction=system_prompt
            )
            
            if context_content:
                full_prompt = f"{context_content}\n\n{user_prompt}"
            else:
                full_prompt = user_prompt
            
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config if generation_config else None,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"QueryEngine streaming failed: {e}")
            raise

    @with_retry(LLM_RETRY_CONFIG)
    def stream_invoke_to_string(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        **kwargs
    ) -> str:
        """
        Stream content and collect into a complete string.
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            **kwargs: Additional generation parameters
            
        Returns:
            Complete generated text
        """
        chunks = []
        for chunk in self.stream_invoke(system_prompt, user_prompt, **kwargs):
            chunks.append(chunk)
        return "".join(chunks)

    @staticmethod
    def validate_response(response: Optional[str]) -> str:
        """Validate and clean response text."""
        if response is None:
            return ""
        return response.strip()

    def get_model_info(self) -> Dict[str, Any]:
        """Return model information."""
        return {
            "provider": self.provider,
            "model": self.model_name,
            "caching_enabled": self.enable_caching,
            "api_base": "native_gemini",
        }
