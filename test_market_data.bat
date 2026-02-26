@echo off
echo Running Market Data Utility Tests...
echo.
echo This tests the anti-hallucination module that anchors LLM outputs
echo to real-time market data (date and stock prices).
echo.

REM Activate conda environment and run market data tests
call "C:\Users\John Jia\miniconda3\Scripts\activate.bat" bettafish

REM Ensure yfinance is installed
pip install yfinance -q

python tests/test_market_data.py

pause
