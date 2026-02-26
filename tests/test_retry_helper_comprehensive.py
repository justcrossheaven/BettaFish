"""
Comprehensive tests for utils/retry_helper.py
Tests retry logic, exponential backoff, jitter, max retries, and error handling.
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests

from utils.retry_helper import (
    with_retry,
    retry_on_network_error,
    with_graceful_retry,
    make_retryable_request,
    RetryConfig,
    DEFAULT_RETRY_CONFIG,
    LLM_RETRY_CONFIG,
    SEARCH_API_RETRY_CONFIG,
    DB_RETRY_CONFIG
)


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config_values(self):
        """Should have correct default values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.backoff_factor == 2.0
        assert config.max_delay == 60.0
        assert config.jitter == False
        assert config.jitter_range == 0.3
    
    def test_custom_config_values(self):
        """Should accept custom configuration."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            backoff_factor=3.0,
            max_delay=120.0,
            jitter=True,
            jitter_range=0.5
        )
        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.backoff_factor == 3.0
        assert config.max_delay == 120.0
        assert config.jitter == True
        assert config.jitter_range == 0.5
    
    def test_default_exception_types(self):
        """Should have default exception types."""
        config = RetryConfig()
        assert requests.exceptions.RequestException in config.retry_on_exceptions
        assert ConnectionError in config.retry_on_exceptions
        assert TimeoutError in config.retry_on_exceptions
    
    def test_custom_exception_types(self):
        """Should accept custom exception types."""
        config = RetryConfig(retry_on_exceptions=(ValueError, KeyError))
        assert ValueError in config.retry_on_exceptions
        assert KeyError in config.retry_on_exceptions


class TestWithRetryDecorator:
    """Test with_retry decorator."""
    
    def test_successful_first_attempt(self):
        """Should succeed on first attempt without retry."""
        call_count = 0
        
        @with_retry()
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = always_succeeds()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_exception(self):
        """Should retry on configured exceptions."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, initial_delay=0.01))
        def fails_twice_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.ConnectionError("Network error")
            return "success"
        
        result = fails_twice_then_succeeds()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Should raise exception after max retries exceeded."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, initial_delay=0.01))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("Network error")
        
        with pytest.raises(requests.exceptions.ConnectionError):
            always_fails()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_exponential_backoff(self):
        """Should implement exponential backoff."""
        call_times = []
        
        @with_retry(RetryConfig(max_retries=3, initial_delay=0.1, backoff_factor=2.0))
        def fails_always():
            call_times.append(time.time())
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            fails_always()
        
        # Check delays are approximately exponential
        assert len(call_times) == 4  # Initial + 3 retries
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 0.09  # Should be ~0.1 seconds
    
    def test_max_delay_cap(self):
        """Should cap delay at max_delay."""
        call_times = []
        
        @with_retry(RetryConfig(
            max_retries=5,
            initial_delay=1.0,
            backoff_factor=10.0,  # Very aggressive
            max_delay=2.0  # But capped
        ))
        def fails_always():
            call_times.append(time.time())
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            fails_always()
        
        # Later delays should be capped at max_delay
        if len(call_times) >= 4:
            delay3 = call_times[3] - call_times[2]
            assert delay3 <= 2.5  # Should be ~2.0, allow some margin
    
    def test_jitter_adds_randomness(self):
        """Should add jitter to delays when enabled."""
        delays = []
        
        for _ in range(3):
            call_times = []
            
            @with_retry(RetryConfig(
                max_retries=2,
                initial_delay=0.1,
                jitter=True,
                jitter_range=0.5
            ))
            def fails_twice():
                call_times.append(time.time())
                if len(call_times) < 3:
                    raise ConnectionError("Error")
                return "success"
            
            fails_twice()
            if len(call_times) >= 2:
                delays.append(call_times[1] - call_times[0])
        
        # Delays should vary due to jitter
        if len(delays) >= 2:
            # Not all delays should be identical
            assert len(set([round(d, 2) for d in delays])) > 1
    
    def test_non_retryable_exception_raised_immediately(self):
        """Should not retry non-configured exceptions."""
        call_count = 0
        
        @with_retry(RetryConfig(retry_on_exceptions=(ConnectionError,)))
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            raises_value_error()
        
        assert call_count == 1  # No retries
    
    def test_503_overload_detection(self):
        """Should detect 503 model overloaded errors."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=1, initial_delay=0.01))
        def raises_503_error():
            nonlocal call_count
            call_count += 1
            raise Exception("503 Service Unavailable: model_overloaded")
        
        with pytest.raises(Exception) as exc_info:
            raises_503_error()
        
        assert "503" in str(exc_info.value) or "overloaded" in str(exc_info.value).lower()
        assert call_count == 2  # Initial + 1 retry
    
    def test_decorator_preserves_function_metadata(self):
        """Should preserve original function name and docstring."""
        @with_retry()
        def my_function():
            """My docstring."""
            return "result"
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."


class TestRetryOnNetworkError:
    """Test retry_on_network_error convenience decorator."""
    
    def test_default_parameters(self):
        """Should use default retry parameters."""
        call_count = 0
        
        @retry_on_network_error()
        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.Timeout("Timeout")
            return "success"
        
        result = network_call()
        assert result == "success"
        assert call_count == 2
    
    def test_custom_max_retries(self):
        """Should accept custom max_retries."""
        call_count = 0
        
        @retry_on_network_error(max_retries=1)
        def network_call():
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("Error")
        
        with pytest.raises(requests.exceptions.ConnectionError):
            network_call()
        
        assert call_count == 2  # Initial + 1 retry


class TestWithGracefulRetry:
    """Test with_graceful_retry decorator."""
    
    def test_returns_default_on_all_failures(self):
        """Should return default value after all retries fail."""
        call_count = 0
        
        @with_graceful_retry(
            RetryConfig(max_retries=2, initial_delay=0.01),
            default_return="fallback"
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Error")
        
        result = always_fails()
        assert result == "fallback"
        assert call_count == 3  # Initial + 2 retries
    
    def test_returns_success_if_succeeds(self):
        """Should return actual result if function succeeds."""
        @with_graceful_retry(default_return="fallback")
        def succeeds():
            return "success"
        
        result = succeeds()
        assert result == "success"
    
    def test_handles_non_retryable_exception(self):
        """Should return default for non-retryable exceptions."""
        @with_graceful_retry(
            RetryConfig(retry_on_exceptions=(ConnectionError,)),
            default_return="default"
        )
        def raises_value_error():
            raise ValueError("Not retryable")
        
        result = raises_value_error()
        assert result == "default"
    
    def test_none_as_default(self):
        """Should handle None as default return value."""
        @with_graceful_retry(default_return=None)
        def always_fails():
            raise Exception("Error")
        
        result = always_fails()
        assert result is None


class TestMakeRetryableRequest:
    """Test make_retryable_request utility function."""
    
    def test_successful_request(self):
        """Should execute request successfully."""
        def my_request():
            return "result"
        
        result = make_retryable_request(my_request)
        assert result == "result"
    
    def test_request_with_args(self):
        """Should pass arguments to request function."""
        def my_request(a, b):
            return a + b
        
        result = make_retryable_request(my_request, 5, 3)
        assert result == 8
    
    def test_request_with_kwargs(self):
        """Should pass keyword arguments to request function."""
        def my_request(x=0, y=0):
            return x * y
        
        result = make_retryable_request(my_request, x=4, y=5)
        assert result == 20
    
    def test_request_with_retries(self):
        """Should retry on failure."""
        call_count = 0
        
        def failing_request():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Error")
            return "success"
        
        result = make_retryable_request(failing_request, max_retries=5)
        assert result == "success"
        assert call_count == 3
    
    def test_custom_max_retries(self):
        """Should respect custom max_retries parameter."""
        call_count = 0
        
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            make_retryable_request(always_fails, max_retries=2)
        
        assert call_count == 3  # Initial + 2 retries


class TestPredefinedConfigs:
    """Test predefined retry configurations."""
    
    def test_llm_retry_config(self):
        """Should have LLM-specific configuration."""
        assert LLM_RETRY_CONFIG.max_retries == 8
        assert LLM_RETRY_CONFIG.initial_delay == 20.0
        assert LLM_RETRY_CONFIG.backoff_factor == 1.8
        assert LLM_RETRY_CONFIG.max_delay == 300.0
        assert LLM_RETRY_CONFIG.jitter == True
    
    def test_search_api_retry_config(self):
        """Should have search API configuration."""
        assert SEARCH_API_RETRY_CONFIG.max_retries == 5
        assert SEARCH_API_RETRY_CONFIG.initial_delay == 2.0
    
    def test_db_retry_config(self):
        """Should have database configuration."""
        assert DB_RETRY_CONFIG.max_retries == 5
        assert DB_RETRY_CONFIG.initial_delay == 1.0


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_zero_retries(self):
        """Should handle zero retries configuration."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=0, initial_delay=0.01))
        def fails_once():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            fails_once()
        
        assert call_count == 1  # Only initial attempt
    
    def test_negative_delay_handled(self):
        """Should handle negative delay (treated as 0)."""
        @with_retry(RetryConfig(max_retries=1, initial_delay=-1.0))
        def test_func():
            return "result"
        
        # Should not crash
        result = test_func()
        assert result == "result"
    
    def test_very_large_backoff_factor(self):
        """Should handle very large backoff factors."""
        call_times = []
        
        @with_retry(RetryConfig(
            max_retries=2,
            initial_delay=0.01,
            backoff_factor=1000.0,
            max_delay=0.5
        ))
        def fails_always():
            call_times.append(time.time())
            raise ConnectionError("Error")
        
        with pytest.raises(ConnectionError):
            fails_always()
        
        # Should be capped by max_delay
        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert delay2 <= 0.6  # Should be ~0.5
