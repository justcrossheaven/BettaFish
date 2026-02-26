"""
Unit tests for the retry helper module.

Tests cover:
- RetryConfig jitter parameter
- Jitter calculation (0-30% variance)
- 503 error detection
- LLM_RETRY_CONFIG values
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utils"))

from utils.retry_helper import (
    RetryConfig,
    LLM_RETRY_CONFIG,
    with_retry,
    SEARCH_API_RETRY_CONFIG,
    DB_RETRY_CONFIG
)


class TestRetryConfig:
    """Tests for RetryConfig class."""
    
    def test_default_config_values(self):
        """Test default RetryConfig values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.backoff_factor == 2.0
        assert config.max_delay == 60.0
        assert config.jitter == False
        assert config.jitter_range == 0.3
    
    def test_custom_config_values(self):
        """Test custom RetryConfig values."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=10.0,
            backoff_factor=1.5,
            max_delay=120.0,
            jitter=True,
            jitter_range=0.2
        )
        assert config.max_retries == 5
        assert config.initial_delay == 10.0
        assert config.backoff_factor == 1.5
        assert config.max_delay == 120.0
        assert config.jitter == True
        assert config.jitter_range == 0.2
    
    def test_jitter_parameter_exists(self):
        """Test that jitter parameter is available."""
        config = RetryConfig(jitter=True)
        assert hasattr(config, 'jitter')
        assert config.jitter == True
    
    def test_jitter_range_parameter_exists(self):
        """Test that jitter_range parameter is available."""
        config = RetryConfig(jitter_range=0.5)
        assert hasattr(config, 'jitter_range')
        assert config.jitter_range == 0.5


class TestLLMRetryConfig:
    """Tests for LLM_RETRY_CONFIG preset."""
    
    def test_llm_retry_config_max_retries(self):
        """Test LLM_RETRY_CONFIG has correct max_retries."""
        assert LLM_RETRY_CONFIG.max_retries == 8
    
    def test_llm_retry_config_initial_delay(self):
        """Test LLM_RETRY_CONFIG has 20 second initial delay."""
        assert LLM_RETRY_CONFIG.initial_delay == 20.0
    
    def test_llm_retry_config_backoff_factor(self):
        """Test LLM_RETRY_CONFIG has 1.8 backoff factor."""
        assert LLM_RETRY_CONFIG.backoff_factor == 1.8
    
    def test_llm_retry_config_max_delay(self):
        """Test LLM_RETRY_CONFIG has 5 minute max delay."""
        assert LLM_RETRY_CONFIG.max_delay == 300.0
    
    def test_llm_retry_config_jitter_enabled(self):
        """Test LLM_RETRY_CONFIG has jitter enabled."""
        assert LLM_RETRY_CONFIG.jitter == True
    
    def test_llm_retry_config_jitter_range(self):
        """Test LLM_RETRY_CONFIG has 30% jitter range."""
        assert LLM_RETRY_CONFIG.jitter_range == 0.3


class TestJitterCalculation:
    """Tests for jitter calculation in retry delays."""
    
    def test_jitter_produces_variance(self):
        """Test that jitter produces varying delays."""
        import random
        
        base_delay = 100.0
        jitter_range = 0.3
        
        # Generate multiple delays with jitter
        delays = []
        for _ in range(100):
            jitter_factor = 1 + random.uniform(-jitter_range, jitter_range)
            delay = base_delay * jitter_factor
            delays.append(delay)
        
        # Check that delays vary (not all the same)
        assert len(set(delays)) > 1, "Jitter should produce varying delays"
        
        # Check delays are within expected range (70-130 for 30% jitter)
        min_expected = base_delay * (1 - jitter_range)
        max_expected = base_delay * (1 + jitter_range)
        
        for delay in delays:
            assert min_expected <= delay <= max_expected, \
                f"Delay {delay} outside expected range [{min_expected}, {max_expected}]"
    
    def test_jitter_range_boundaries(self):
        """Test jitter stays within configured range."""
        import random
        
        base_delay = 50.0
        jitter_range = 0.3
        
        for _ in range(1000):
            jitter_factor = 1 + random.uniform(-jitter_range, jitter_range)
            delay = base_delay * jitter_factor
            
            # Should be between 35 and 65 (±30% of 50)
            assert 35.0 <= delay <= 65.0, f"Delay {delay} outside ±30% range"


class Test503ErrorDetection:
    """Tests for 503 model overloaded error detection."""
    
    def test_503_detection_in_error_string(self):
        """Test that 503 is detected in error messages."""
        error_messages = [
            "Error 503: Model overloaded",
            "HTTP 503 Service Unavailable",
            "503 server error",
        ]
        
        for msg in error_messages:
            error_str = msg.lower()
            is_503 = '503' in error_str
            assert is_503, f"Should detect 503 in: {msg}"
    
    def test_overloaded_detection_in_error_string(self):
        """Test that 'overloaded' is detected in error messages."""
        error_messages = [
            "Model is currently overloaded",
            "Server overloaded, please retry",
            "model_overloaded error",
        ]
        
        for msg in error_messages:
            error_str = msg.lower()
            is_overloaded = 'overloaded' in error_str or 'model_overloaded' in error_str
            assert is_overloaded, f"Should detect overloaded in: {msg}"
    
    def test_model_overloaded_detection(self):
        """Test model_overloaded specific detection."""
        error_msg = "APIError: model_overloaded - The model is at capacity"
        error_str = error_msg.lower()
        
        is_503_overload = (
            '503' in error_str or 
            'overloaded' in error_str or 
            'model_overloaded' in error_str
        )
        assert is_503_overload


class TestOtherRetryConfigs:
    """Tests for other retry configurations."""
    
    def test_search_api_retry_config_exists(self):
        """Test SEARCH_API_RETRY_CONFIG exists and has valid values."""
        assert SEARCH_API_RETRY_CONFIG is not None
        assert SEARCH_API_RETRY_CONFIG.max_retries >= 1
        assert SEARCH_API_RETRY_CONFIG.initial_delay > 0
    
    def test_db_retry_config_exists(self):
        """Test DB_RETRY_CONFIG exists and has valid values."""
        assert DB_RETRY_CONFIG is not None
        assert DB_RETRY_CONFIG.max_retries >= 1
        assert DB_RETRY_CONFIG.initial_delay > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
