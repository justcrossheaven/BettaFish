# BettaFish Test Suite

Comprehensive test suite for the BettaFish trade and investment analysis platform.

## 📋 Test Coverage

### Unit Tests (80%+ coverage target)

#### Core Utils
- ✅ `test_market_data_comprehensive.py` - Market data ticker extraction, snapshot fetching, fallback behavior
- ✅ `test_gemini_cache_comprehensive.py` - Gemini cache manager, hash stability, explicit/implicit caching
- ✅ `test_retry_helper_comprehensive.py` - Retry logic, exponential backoff, jitter
- ✅ `test_financial_terminology.py` - Financial term lookups, category completeness

#### Social Media Clients
- ✅ `test_reddit_client.py` - Reddit client (PRAW mocked)
- ✅ `test_twitter_client.py` - Twitter client (twikit mocked)

#### Query Engine Tools
- ✅ `test_query_engine_tools.py` - Reddit/Twitter search functionality (mocked)

#### Prompts
- ✅ `test_engine_prompts.py` - Schema validity, prompt generation for InsightEngine, MediaEngine, QueryEngine

### End-to-End Tests
- ✅ `test_flask_web_ui.py` - Flask web UI with Playwright
  - Page loads
  - Query submission
  - Progress updates (mocked)
  - Report generation (mocked)
  - Error handling

### Test Infrastructure
- ✅ `conftest.py` - Shared fixtures and configuration
- ✅ `mocks/` - Reusable mock objects
  - `mock_yfinance.py` - Mock yfinance for market data
  - `mock_praw.py` - Mock PRAW for Reddit
  - `mock_twikit.py` - Mock twikit for Twitter
  - `mock_gemini.py` - Mock Google Generative AI

## 🚀 Running Tests

### Prerequisites

```bash
# Activate virtual environment
cd /home/clawdbot/.openclaw/workspace-agents/code/BettaFish
source .venv/bin/activate

# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-asyncio playwright
playwright install chromium
```

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests (fast)
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration

# Run only E2E tests
pytest tests/ -v -m e2e

# Exclude slow tests
pytest tests/ -v -m "not slow"
```

### Run Individual Test Files

```bash
# Test market data
pytest tests/test_market_data_comprehensive.py -v

# Test retry helper
pytest tests/test_retry_helper_comprehensive.py -v

# Test Gemini cache
pytest tests/test_gemini_cache_comprehensive.py -v

# Test financial terminology
pytest tests/test_financial_terminology.py -v

# Test Reddit client
pytest tests/test_reddit_client.py -v

# Test Twitter client
pytest tests/test_twitter_client.py -v

# Test QueryEngine tools
pytest tests/test_query_engine_tools.py -v

# Test prompts
pytest tests/test_engine_prompts.py -v

# Test E2E (requires Flask app or mocks)
pytest tests/e2e/test_flask_web_ui.py -v
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_market_data_comprehensive.py::TestTickerExtraction -v

# Run specific test function
pytest tests/test_market_data_comprehensive.py::TestTickerExtraction::test_extract_ticker_from_company_name -v
```

## 📊 Coverage Reports

### View Coverage in Terminal
```bash
pytest tests/ --cov --cov-report=term-missing
```

### Generate HTML Coverage Report
```bash
pytest tests/ --cov --cov-report=html
# Open htmlcov/index.html in browser
```

### Check Coverage Threshold
```bash
# Fail if coverage below 80%
pytest tests/ --cov --cov-fail-under=80
```

## 🔧 Configuration

Test configuration is in `pytest.ini`:

- Coverage threshold: 80%
- Test discovery: `test_*.py` files
- Markers: unit, integration, e2e, slow
- Async support: enabled
- Coverage reports: terminal, HTML, XML

## 🧪 Writing New Tests

### Test File Naming
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`
- E2E tests: `tests/e2e/test_<feature>.py`

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """Test description."""
    
    def test_specific_behavior(self):
        """Should do something specific."""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_output
```

### Using Fixtures
```python
def test_with_fixture(mock_yfinance_ticker, sample_market_snapshot):
    """Use shared fixtures from conftest.py"""
    # Fixtures are automatically injected
    assert sample_market_snapshot['ticker'] == 'MSFT'
```

### Async Tests
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

## 🐛 Debugging Tests

### Run Tests with Print Statements
```bash
pytest tests/ -v -s  # -s shows print() output
```

### Run Tests with Debugger
```bash
pytest tests/ -v --pdb  # Drop into pdb on failure
```

### Run Only Failed Tests
```bash
pytest tests/ --lf  # Last failed
pytest tests/ --ff  # Failed first
```

### Show Test Duration
```bash
pytest tests/ -v --durations=10  # Show 10 slowest tests
```

## 📝 Test Markers

### Available Markers
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.asyncio` - Async tests

### Using Markers
```python
@pytest.mark.unit
@pytest.mark.slow
def test_complex_calculation():
    """This test is both a unit test and slow."""
    pass
```

## 🔐 Environment Variables for Testing

Some tests require environment variables:

```bash
# Reddit API credentials (optional for tests, mocked by default)
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"

# Twitter API credentials (optional for tests, mocked by default)
export TWITTER_USERNAME="your_username"
export TWITTER_EMAIL="your_email"
export TWITTER_PASSWORD="your_password"

# Gemini API (optional for tests, mocked by default)
export GEMINI_API_KEY="your_api_key"
```

**Note:** Tests use mocks by default, so credentials are not required for testing.

## 📈 Current Coverage Status

Target: 80%+ coverage on new code

### Covered Modules
- ✅ utils/market_data.py
- ✅ utils/gemini_cache_manager.py
- ✅ utils/retry_helper.py
- ✅ prompts/financial_terminology.py
- ✅ MindSpider/.../reddit/client.py
- ✅ MindSpider/.../twitter/client.py
- ✅ QueryEngine/tools/reddit_search.py
- ✅ QueryEngine/tools/twitter_search.py
- ✅ InsightEngine/prompts/prompts.py
- ✅ MediaEngine/prompts/prompts.py
- ✅ QueryEngine/prompts/prompts.py

## 🤝 Contributing Tests

When adding new features, please:

1. Write tests alongside code
2. Aim for 80%+ coverage
3. Use appropriate test markers
4. Mock external dependencies
5. Add fixtures to `conftest.py` if reusable
6. Update this README with new test files

## 🔍 Troubleshooting

### Import Errors
```bash
# Make sure you're in the project root
cd /home/clawdbot/.openclaw/workspace-agents/code/BettaFish

# Ensure virtual environment is activated
source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt
```

### Module Not Found
```bash
# Check PYTHONPATH
export PYTHONPATH=/home/clawdbot/.openclaw/workspace-agents/code/BettaFish:$PYTHONPATH
```

### Async Test Failures
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
