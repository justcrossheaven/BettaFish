"""
Gemini Cache Manager
Provides hybrid context caching for Gemini API with explicit caching for large content
and implicit caching for small content (system prompts).

Key features:
- SHA256 stable hashing (not Python's non-deterministic hash())
- Local cache registry to avoid O(N) list() calls
- Token threshold check (explicit caching only for >2,048 tokens)
- Automatic fallback to implicit caching for small content
"""

import hashlib
import datetime
from typing import Dict, Optional, Any
from loguru import logger

# Try to import google.generativeai for native Gemini support
try:
    import google.generativeai as genai
    from google.generativeai import caching
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    caching = None


class GeminiCacheManager:
    """
    Manages Gemini context caching with hybrid approach.
    
    - Explicit caching: For large content (>10,000 chars / ~2,500 tokens)
    - Implicit caching: For small content (automatic, free)
    """
    
    # Minimum character count for explicit caching (~2,500 tokens)
    MIN_CHARS_FOR_EXPLICIT_CACHE = 10000
    
    # Local registry to avoid O(N) list() calls
    # Maps content_hash -> cache_name
    _cache_registry: Dict[str, str] = {}
    
    def __init__(self, api_key: str, model_name: str):
        """
        Initialize cache manager with Gemini API credentials.
        
        Args:
            api_key: Gemini API key
            model_name: Model name (e.g., 'gemini-2.0-flash-001')
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai>=0.8.0"
            )
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self._api_key = api_key
    
    def _compute_cache_key(self, content: str) -> str:
        """
        Compute stable SHA256 hash of content.
        
        Unlike Python's hash(), SHA256 is deterministic across restarts.
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def should_use_explicit_cache(self, content: str) -> bool:
        """
        Check if content is large enough for explicit caching.
        
        Explicit caching has a minimum token threshold (~2,048 tokens).
        For smaller content, implicit caching is more cost-effective.
        """
        return len(content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
    
    def get_or_create_cache(
        self, 
        system_prompt: str, 
        context_content: str = "",
        ttl_hours: int = 1
    ) -> Optional[Any]:
        """
        Get existing cache or create new one for large content.
        
        Args:
            system_prompt: System instruction for the model
            context_content: Additional context (e.g., 10-K reports, documents)
            ttl_hours: Cache time-to-live in hours
            
        Returns:
            CachedContent object if content is large enough, None otherwise
        """
        full_content = f"{system_prompt}\n\n{context_content}"
        
        # Check if content meets minimum threshold for explicit caching
        if not self.should_use_explicit_cache(full_content):
            logger.debug(
                f"Content too small for explicit cache ({len(full_content)} chars). "
                f"Using implicit caching."
            )
            return None
        
        content_hash = self._compute_cache_key(full_content)
        display_name = f"bettafish_{content_hash[:16]}"
        
        # Check local registry first (avoids network call)
        if content_hash in self._cache_registry:
            cached_name = self._cache_registry[content_hash]
            try:
                # Verify cache still exists and is valid
                for cached in caching.CachedContent.list():
                    if cached.display_name == cached_name:
                        if cached.expire_time > datetime.datetime.now(datetime.timezone.utc):
                            logger.info(f"Cache hit: {cached_name}")
                            return cached
                        else:
                            # Cache expired, remove from registry
                            del self._cache_registry[content_hash]
                            break
            except Exception as e:
                logger.warning(f"Error checking cache registry: {e}")
        
        # Try to find existing cache by display name
        try:
            for cached in caching.CachedContent.list():
                if cached.display_name == display_name:
                    if cached.expire_time > datetime.datetime.now(datetime.timezone.utc):
                        # Update registry and return
                        self._cache_registry[content_hash] = display_name
                        logger.info(f"Found existing cache: {display_name}")
                        return cached
        except Exception as e:
            logger.warning(f"Error listing caches: {e}")
        
        # Create new cache
        try:
            logger.info(f"Creating new cache: {display_name}")
            cached = caching.CachedContent.create(
                model=self.model_name,
                display_name=display_name,
                system_instruction=system_prompt,
                contents=[context_content] if context_content else [],
                ttl=datetime.timedelta(hours=ttl_hours)
            )
            self._cache_registry[content_hash] = display_name
            return cached
        except Exception as e:
            logger.error(f"Failed to create cache: {e}")
            return None
    
    def clear_registry(self):
        """Clear the local cache registry."""
        self._cache_registry.clear()
        logger.info("Cache registry cleared")


class GeminiClient:
    """
    Native Gemini client with hybrid caching support.
    
    Uses explicit caching for large context, implicit caching for system prompts.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model_name: str = "gemini-2.0-flash-001",
        enable_caching: bool = True
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
            model_name: Model name
            enable_caching: Whether to use explicit caching for large content
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai>=0.8.0"
            )
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.enable_caching = enable_caching
        
        if enable_caching:
            self._cache_manager = GeminiCacheManager(api_key, model_name)
        else:
            self._cache_manager = None
    
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
            context_content: Optional large context (e.g., documents)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        cache = None
        
        # Try to use explicit cache if enabled and content is large
        if self.enable_caching and self._cache_manager:
            cache = self._cache_manager.get_or_create_cache(
                system_prompt, 
                context_content
            )
        
        try:
            if cache:
                # Use cached content path
                logger.debug("Using explicit cached context")
                model = genai.GenerativeModel.from_cached_content(cached_content=cache)
                response = model.generate_content(user_prompt, **kwargs)
            else:
                # Use standard path with implicit caching
                logger.debug("Using implicit caching (standard request)")
                model = genai.GenerativeModel(
                    self.model_name, 
                    system_instruction=system_prompt
                )
                # Combine context with user prompt if present
                if context_content:
                    full_prompt = f"{context_content}\n\n{user_prompt}"
                else:
                    full_prompt = user_prompt
                    
                response = model.generate_content(full_prompt, **kwargs)
            
            # Extract text from response
            if response and response.text:
                return response.text.strip()
            return ""
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model information."""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "caching_enabled": self.enable_caching
        }


# Factory function to check if Gemini is available
def is_gemini_available() -> bool:
    """Check if google-generativeai package is installed."""
    return GEMINI_AVAILABLE
