"""
Mock Google Generative AI module for testing Gemini functionality.
"""

import datetime
from unittest.mock import Mock, MagicMock


class MockGemini:
    """Mock implementation of google.generativeai for testing."""
    
    @staticmethod
    def create_cached_content(name="test_cache", display_name="bettafish_abc123"):
        """Create a mock CachedContent object."""
        cached = Mock()
        cached.name = name
        cached.display_name = display_name
        cached.expire_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        cached.create_time = datetime.datetime.now(datetime.timezone.utc)
        return cached
    
    @staticmethod
    def create_expired_cached_content(name="expired_cache"):
        """Create a mock expired CachedContent."""
        cached = Mock()
        cached.name = name
        cached.display_name = "bettafish_expired"
        cached.expire_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        return cached
    
    @staticmethod
    def create_response(text="Generated response"):
        """Create a mock GenerativeModel response."""
        response = Mock()
        response.text = text
        return response
    
    @staticmethod
    def create_model():
        """Create a mock GenerativeModel."""
        model = Mock()
        model.generate_content = Mock(return_value=MockGemini.create_response())
        return model
    
    @staticmethod
    def create_caching_module():
        """Create a mock caching module."""
        caching = Mock()
        
        # Mock CachedContent class
        caching.CachedContent = Mock()
        
        # Mock list method
        caching.CachedContent.list = Mock(return_value=[
            MockGemini.create_cached_content("cache1", "bettafish_abc123"),
            MockGemini.create_cached_content("cache2", "bettafish_def456")
        ])
        
        # Mock create method
        def mock_create(**kwargs):
            return MockGemini.create_cached_content(
                display_name=kwargs.get('display_name', 'bettafish_test')
            )
        
        caching.CachedContent.create = Mock(side_effect=mock_create)
        
        return caching
    
    @staticmethod
    def create_genai_module():
        """Create a mock google.generativeai module."""
        genai = Mock()
        
        # Mock configure
        genai.configure = Mock()
        
        # Mock GenerativeModel class
        genai.GenerativeModel = Mock(return_value=MockGemini.create_model())
        
        # Mock from_cached_content
        genai.GenerativeModel.from_cached_content = Mock(
            return_value=MockGemini.create_model()
        )
        
        # Mock caching
        genai.caching = MockGemini.create_caching_module()
        
        return genai
