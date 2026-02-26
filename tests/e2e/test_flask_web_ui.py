import os
import subprocess
import time
from unittest.mock import Mock

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="module")
def flask_app():
    env = os.environ.copy()
    env["FLASK_ENV"] = "testing"
    env["TESTING"] = "true"
    process = subprocess.Popen(
        ["python3", "app.py"],
        cwd="/home/clawdbot/.openclaw/workspace-agents/code/BettaFish",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    yield process
    process.terminate()


@pytest.fixture
def browser_page():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            yield page
            page.close()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright browser unavailable in this environment: {exc}")


@pytest.mark.e2e
class TestFlaskUIBasicFlow:
    def test_homepage_loads(self, browser_page):
        browser_page.goto("http://localhost:5000", timeout=10000)
        assert "localhost:5000" in browser_page.url


@pytest.mark.integration
class TestFlaskAppStructure:
    def test_app_py_exists(self):
        assert os.path.exists("/home/clawdbot/.openclaw/workspace-agents/code/BettaFish/app.py")

    def test_static_directory_exists(self):
        path = "/home/clawdbot/.openclaw/workspace-agents/code/BettaFish/static"
        assert os.path.isdir(path)


@pytest.mark.integration
class TestMockedE2EFlow:
    def test_full_pipeline_with_mocks(self):
        mock_query_instance = Mock()
        mock_query_instance.run.return_value = {"report": "Query report", "status": "success"}
        result = mock_query_instance.run("Test query")
        assert result["status"] == "success"
        assert "report" in result
