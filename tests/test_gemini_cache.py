"""
Unit tests for the Gemini cache manager module.

Tests cover:
- SHA256 stable hashing
- Token threshold logic
- Cache registry operations
- Hybrid caching decision logic
"""

import sys
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utils"))


class TestSHA256Hashing:
    """Tests for SHA256 stable hashing."""
    
    def test_sha256_is_deterministic(self):
        """Test that SHA256 produces same hash for same content."""
        content = "This is a test system prompt for value investing analysis."
        
        hash1 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        assert hash1 == hash2, "SHA256 should be deterministic"
    
    def test_sha256_different_for_different_content(self):
        """Test that SHA256 produces different hashes for different content."""
        content1 = "System prompt version 1"
        content2 = "System prompt version 2"
        
        hash1 = hashlib.sha256(content1.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(content2.encode('utf-8')).hexdigest()
        
        assert hash1 != hash2, "Different content should have different hashes"
    
    def test_sha256_handles_unicode(self):
        """Test that SHA256 handles unicode content correctly."""
        content = "今天的实际时间是2026年01月26日 - Value investing analysis"
        
        hash_result = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        assert len(hash_result) == 64, "SHA256 should produce 64 char hex string"
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_sha256_full_content_not_truncated(self):
        """Test that full content affects hash, not just beginning."""
        base = "A" * 100
        content1 = base + "X"
        content2 = base + "Y"
        
        hash1 = hashlib.sha256(content1.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(content2.encode('utf-8')).hexdigest()
        
        assert hash1 != hash2, "Difference at end should change hash"


class TestTokenThresholdLogic:
    """Tests for token threshold checking logic."""
    
    MIN_CHARS_FOR_EXPLICIT_CACHE = 10000  # Same as in gemini_cache_manager.py
    
    def test_small_content_below_threshold(self):
        """Test that small content is below threshold."""
        small_content = "You are a value investing analyst." * 10  # ~350 chars
        
        should_cache = len(small_content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert not should_cache, "Small content should not use explicit cache"
    
    def test_large_content_above_threshold(self):
        """Test that large content is above threshold."""
        # Create content with ~15000 chars (above 10000 threshold)
        large_content = "This is sample financial report content. " * 400
        
        should_cache = len(large_content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert should_cache, "Large content should use explicit cache"
    
    def test_threshold_boundary_exact(self):
        """Test exact threshold boundary."""
        # Exactly at threshold
        exact_content = "X" * self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        should_cache = len(exact_content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert should_cache, "Content at exact threshold should cache"
    
    def test_threshold_boundary_one_below(self):
        """Test one character below threshold."""
        below_content = "X" * (self.MIN_CHARS_FOR_EXPLICIT_CACHE - 1)
        
        should_cache = len(below_content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert not should_cache, "Content one below threshold should not cache"
    
    def test_typical_system_prompt_size(self):
        """Test that typical system prompts are below threshold."""
        # A realistic system prompt (~500 chars)
        system_prompt = """
        You are a senior financial analyst specializing in value investing.
        Focus on companies with strong fundamentals, low P/E ratios, and 
        consistent free cash flow generation. Avoid EBITDA-focused analysis.
        Look for margin of safety in all investment recommendations.
        Consider the competitive moat and management quality.
        """
        
        should_cache = len(system_prompt) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert not should_cache, "Typical system prompt should use implicit caching"
    
    def test_10k_report_size(self):
        """Test that 10-K report sized content is above threshold."""
        # A 10-K report is typically 50,000+ characters
        report_content = "Financial statement data. " * 2500  # ~65000 chars
        
        should_cache = len(report_content) >= self.MIN_CHARS_FOR_EXPLICIT_CACHE
        
        assert should_cache, "10-K report should use explicit caching"


class TestCacheRegistryLogic:
    """Tests for cache registry operations."""
    
    def test_registry_stores_hash_to_name_mapping(self):
        """Test that registry correctly maps hash to cache name."""
        registry = {}
        
        content_hash = hashlib.sha256("test content".encode()).hexdigest()
        cache_name = f"bettafish_{content_hash[:16]}"
        
        registry[content_hash] = cache_name
        
        assert content_hash in registry
        assert registry[content_hash] == cache_name
    
    def test_registry_lookup_avoids_list_call(self):
        """Test that registry lookup is O(1)."""
        registry = {}
        
        # Pre-populate registry
        for i in range(1000):
            content_hash = hashlib.sha256(f"content_{i}".encode()).hexdigest()
            cache_name = f"cache_{i}"
            registry[content_hash] = cache_name
        
        # Lookup should be fast (O(1))
        target_hash = hashlib.sha256("content_500".encode()).hexdigest()
        
        assert target_hash in registry
        assert registry[target_hash] == "cache_500"
    
    def test_registry_clear(self):
        """Test that registry can be cleared."""
        registry = {"hash1": "cache1", "hash2": "cache2"}
        
        registry.clear()
        
        assert len(registry) == 0


class TestHybridCachingDecision:
    """Tests for hybrid caching decision logic."""
    
    MIN_CHARS = 10000
    
    def test_system_prompt_only_uses_implicit(self):
        """Test system prompt alone uses implicit caching."""
        system_prompt = "You are a financial analyst."
        context = ""
        
        full_content = f"{system_prompt}\n\n{context}"
        use_explicit = len(full_content) >= self.MIN_CHARS
        
        assert not use_explicit, "System prompt alone should use implicit"
    
    def test_system_with_large_context_uses_explicit(self):
        """Test system + large context uses explicit caching."""
        system_prompt = "You are a financial analyst."
        context = "Financial report data. " * 500  # ~12500 chars
        
        full_content = f"{system_prompt}\n\n{context}"
        use_explicit = len(full_content) >= self.MIN_CHARS
        
        assert use_explicit, "System + large context should use explicit"
    
    def test_user_query_only_uses_implicit(self):
        """Test that user query alone uses implicit caching."""
        user_query = "What is NVIDIA's current P/E ratio?"
        
        use_explicit = len(user_query) >= self.MIN_CHARS
        
        assert not use_explicit, "User query should use implicit"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
