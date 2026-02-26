"""
Comprehensive tests for utils/gemini_cache_manager.py
Tests cache hit/miss, hash stability, explicit vs implicit caching, expiry.
"""

import pytest
import hashlib
import datetime
from unittest.mock import Mock, patch, MagicMock

from utils.gemini_cache_manager import (
    GeminiCacheManager,
    GeminiClient,
    is_gemini_available,
    GEMINI_AVAILABLE
)
from tests.mocks import MockGemini


class TestGeminiAvailability:
    """Test Gemini availability checking."""
    
    def test_is_gemini_available(self):
        """Should check if gemini is available."""
        # This will be True if google-generativeai is installed
        available = is_gemini_available()
        assert isinstance(available, bool)
    
    @patch('utils.gemini_cache_manager.GEMINI_AVAILABLE', False)
    def test_cache_manager_import_error(self):
        """Should raise ImportError when gemini not available."""
        with pytest.raises(ImportError) as exc_info:
            GeminiCacheManager("fake_key", "gemini-2.0-flash-001")
        
        assert "google-generativeai" in str(exc_info.value).lower()


@pytest.mark.skipif(not GEMINI_AVAILABLE, reason="google-generativeai not installed")
class TestGeminiCacheManager:
    """Test GeminiCacheManager class."""
    
    def test_initialization(self):
        """Should initialize with API key and model."""
        manager = GeminiCacheManager("test_api_key", "gemini-2.0-flash-001")
        assert manager.model_name == "gemini-2.0-flash-001"
        assert manager._api_key == "test_api_key"
    
    def test_compute_cache_key_stability(self):
        """Should compute stable SHA256 hash."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        content = "Test content for hashing"
        hash1 = manager._compute_cache_key(content)
        hash2 = manager._compute_cache_key(content)
        
        # Should be identical (deterministic)
        assert hash1 == hash2
        
        # Should be valid SHA256 (64 hex characters)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_compute_cache_key_different_content(self):
        """Should produce different hashes for different content."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        hash1 = manager._compute_cache_key("Content A")
        hash2 = manager._compute_cache_key("Content B")
        
        assert hash1 != hash2
    
    def test_compute_cache_key_unicode(self):
        """Should handle Unicode content."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        content = "测试内容 🚀 مرحبا"
        hash_result = manager._compute_cache_key(content)
        
        assert len(hash_result) == 64
    
    def test_should_use_explicit_cache_small_content(self):
        """Should return False for small content."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        small_content = "x" * 5000  # 5,000 chars
        assert manager.should_use_explicit_cache(small_content) == False
    
    def test_should_use_explicit_cache_large_content(self):
        """Should return True for large content."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        large_content = "x" * 15000  # 15,000 chars
        assert manager.should_use_explicit_cache(large_content) == True
    
    def test_should_use_explicit_cache_threshold(self):
        """Should use threshold of 10,000 characters."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        # Just below threshold
        assert manager.should_use_explicit_cache("x" * 9999) == False
        
        # At threshold
        assert manager.should_use_explicit_cache("x" * 10000) == True
        
        # Above threshold
        assert manager.should_use_explicit_cache("x" * 10001) == True
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_get_or_create_cache_small_content_returns_none(self, mock_caching, mock_genai):
        """Should return None for small content (implicit caching)."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        result = manager.get_or_create_cache(
            system_prompt="Short prompt",
            context_content="Short context"
        )
        
        assert result is None
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_get_or_create_cache_large_content_creates_cache(self, mock_caching, mock_genai):
        """Should create cache for large content."""
        # Setup mocks
        mock_caching.CachedContent.list.return_value = []
        mock_cached = MockGemini.create_cached_content()
        mock_caching.CachedContent.create.return_value = mock_cached
        
        manager = GeminiCacheManager("test_key", "test_model")
        
        large_content = "x" * 15000
        result = manager.get_or_create_cache(
            system_prompt="System",
            context_content=large_content
        )
        
        # Should create cache
        mock_caching.CachedContent.create.assert_called_once()
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_get_or_create_cache_hit_in_registry(self, mock_caching, mock_genai):
        """Should hit cache from local registry."""
        # Setup: existing cache
        mock_cached = MockGemini.create_cached_content(
            display_name="bettafish_abc123"
        )
        mock_caching.CachedContent.list.return_value = [mock_cached]
        
        manager = GeminiCacheManager("test_key", "test_model")
        
        # Pre-populate registry
        large_content = "x" * 15000
        content_hash = manager._compute_cache_key(f"System\n\n{large_content}")
        manager._cache_registry[content_hash] = "bettafish_abc123"
        
        # First call should hit registry
        result = manager.get_or_create_cache(
            system_prompt="System",
            context_content=large_content
        )
        
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_get_or_create_cache_expired_removed_from_registry(self, mock_caching, mock_genai):
        """Should remove expired cache from registry."""
        # Setup: expired cache
        expired_cache = MockGemini.create_expired_cached_content()
        mock_caching.CachedContent.list.return_value = [expired_cache]
        
        # Create new cache when not found
        new_cache = MockGemini.create_cached_content("new_cache")
        mock_caching.CachedContent.create.return_value = new_cache
        
        manager = GeminiCacheManager("test_key", "test_model")
        
        # Pre-populate with expired cache
        large_content = "x" * 15000
        content_hash = manager._compute_cache_key(f"System\n\n{large_content}")
        manager._cache_registry[content_hash] = "expired_cache"
        
        result = manager.get_or_create_cache(
            system_prompt="System",
            context_content=large_content
        )
        
        # Should create new cache
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_get_or_create_cache_custom_ttl(self, mock_caching, mock_genai):
        """Should respect custom TTL parameter."""
        mock_caching.CachedContent.list.return_value = []
        mock_cached = MockGemini.create_cached_content()
        mock_caching.CachedContent.create.return_value = mock_cached
        
        manager = GeminiCacheManager("test_key", "test_model")
        
        large_content = "x" * 15000
        manager.get_or_create_cache(
            system_prompt="System",
            context_content=large_content,
            ttl_hours=3
        )
        
        # Check that TTL was passed
        call_args = mock_caching.CachedContent.create.call_args
        assert call_args is not None
        # TTL should be a timedelta of 3 hours
        assert 'ttl' in call_args[1]
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_clear_registry(self, mock_caching, mock_genai):
        """Should clear local cache registry."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        # Populate registry
        manager._cache_registry["hash1"] = "cache1"
        manager._cache_registry["hash2"] = "cache2"
        assert len(manager._cache_registry) == 2
        
        # Clear
        manager.clear_registry()
        assert len(manager._cache_registry) == 0
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_cache_name_format(self, mock_caching, mock_genai):
        """Should use 'bettafish_' prefix and first 16 chars of hash."""
        mock_caching.CachedContent.list.return_value = []
        mock_cached = MockGemini.create_cached_content()
        mock_caching.CachedContent.create.return_value = mock_cached
        
        manager = GeminiCacheManager("test_key", "test_model")
        
        large_content = "x" * 15000
        manager.get_or_create_cache(
            system_prompt="System",
            context_content=large_content
        )
        
        call_args = mock_caching.CachedContent.create.call_args
        display_name = call_args[1]['display_name']
        
        assert display_name.startswith("bettafish_")
        # Name should be prefix + 16 hex chars
        assert len(display_name) == len("bettafish_") + 16


@pytest.mark.skipif(not GEMINI_AVAILABLE, reason="google-generativeai not installed")
class TestGeminiClient:
    """Test GeminiClient class."""
    
    def test_client_initialization(self):
        """Should initialize with default parameters."""
        client = GeminiClient("test_api_key")
        assert client.model_name == "gemini-2.0-flash-001"
        assert client.enable_caching == True
    
    def test_client_initialization_custom_model(self):
        """Should accept custom model name."""
        client = GeminiClient("test_api_key", model_name="gemini-3.0-pro")
        assert client.model_name == "gemini-3.0-pro"
    
    def test_client_initialization_caching_disabled(self):
        """Should allow disabling caching."""
        client = GeminiClient("test_api_key", enable_caching=False)
        assert client.enable_caching == False
        assert client._cache_manager is None
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_small_content_implicit_cache(self, mock_genai):
        """Should use implicit caching for small content."""
        mock_model = MockGemini.create_model()
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key")
        
        result = client.invoke(
            system_prompt="Short system prompt",
            user_prompt="What is AI?",
            context_content="Small context"
        )
        
        # Should use standard GenerativeModel
        mock_genai.GenerativeModel.assert_called_once()
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    @patch('utils.gemini_cache_manager.caching')
    def test_invoke_large_content_explicit_cache(self, mock_caching, mock_genai):
        """Should use explicit caching for large content."""
        mock_cached = MockGemini.create_cached_content()
        mock_caching.CachedContent.create.return_value = mock_cached
        mock_caching.CachedContent.list.return_value = []
        
        mock_model = MockGemini.create_model()
        mock_genai.GenerativeModel.from_cached_content.return_value = mock_model
        
        client = GeminiClient("test_api_key", enable_caching=True)
        
        large_content = "x" * 15000
        result = client.invoke(
            system_prompt="System",
            user_prompt="Analyze this",
            context_content=large_content
        )
        
        # Should use cached content path
        mock_genai.GenerativeModel.from_cached_content.assert_called_once()
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_caching_disabled(self, mock_genai):
        """Should skip caching when disabled."""
        mock_model = MockGemini.create_model()
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key", enable_caching=False)
        
        large_content = "x" * 15000
        result = client.invoke(
            system_prompt="System",
            user_prompt="Analyze this",
            context_content=large_content
        )
        
        # Should use standard path even with large content
        mock_genai.GenerativeModel.assert_called_once()
        assert result is not None
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_combines_context_with_user_prompt(self, mock_genai):
        """Should combine context with user prompt when not cached."""
        mock_model = MockGemini.create_model()
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key")
        
        client.invoke(
            system_prompt="System",
            user_prompt="User question",
            context_content="Additional context"
        )
        
        # Should call generate_content with combined prompt
        mock_model.generate_content.assert_called_once()
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Additional context" in call_args
        assert "User question" in call_args
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_handles_empty_response(self, mock_genai):
        """Should handle empty response gracefully."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key")
        
        result = client.invoke(
            system_prompt="System",
            user_prompt="Question"
        )
        
        assert result == ""
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_strips_whitespace(self, mock_genai):
        """Should strip whitespace from response."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "  Response with spaces  \n"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key")
        
        result = client.invoke(
            system_prompt="System",
            user_prompt="Question"
        )
        
        assert result == "Response with spaces"
    
    @patch('utils.gemini_cache_manager.genai')
    def test_invoke_raises_on_error(self, mock_genai):
        """Should raise exception on generation error."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("test_api_key")
        
        with pytest.raises(Exception) as exc_info:
            client.invoke(
                system_prompt="System",
                user_prompt="Question"
            )
        
        assert "API Error" in str(exc_info.value)
    
    def test_get_model_info(self):
        """Should return model information."""
        client = GeminiClient("test_api_key", model_name="gemini-3.0-pro", enable_caching=True)
        
        info = client.get_model_info()
        
        assert info['provider'] == "gemini"
        assert info['model'] == "gemini-3.0-pro"
        assert info['caching_enabled'] == True


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.skipif(not GEMINI_AVAILABLE, reason="google-generativeai not installed")
    def test_empty_content_hash(self):
        """Should handle empty content for hashing."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        result = manager._compute_cache_key("")
        assert len(result) == 64
    
    @pytest.mark.skipif(not GEMINI_AVAILABLE, reason="google-generativeai not installed")
    def test_very_long_content_hash(self):
        """Should handle very long content."""
        manager = GeminiCacheManager("test_key", "test_model")
        
        very_long = "x" * 1000000  # 1 million chars
        result = manager._compute_cache_key(very_long)
        assert len(result) == 64
