@echo off
echo Testing Twitter and Reddit module availability...
echo.

REM Activate conda environment and test imports
call "C:\Users\John Jia\miniconda3\Scripts\activate.bat" bettafish

echo [1/3] Testing QueryEngine.tools imports...
python -c "from QueryEngine.tools import TwitterSearchClient, RedditSearchClient; print('✓ QueryEngine tools import successful')"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ QueryEngine tools import FAILED
    pause
    exit /b 1
)
echo.

echo [2/3] Testing MindSpider platform modules...
python -c "from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.twitter import TwitterClient; from MindSpider.DeepSentimentCrawling.MediaCrawler.media_platform.reddit import RedditClient; print('✓ MindSpider platform modules import successful')"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ MindSpider platform modules import FAILED
    pause
    exit /b 1
)
echo.

echo [3/3] Testing library availability...
python -c "import twikit; import praw; print('✓ twikit and praw libraries available')"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Library check FAILED
    pause
    exit /b 1
)
echo.

echo ========================================
echo All Twitter and Reddit modules are available!
echo ========================================
echo.
echo Next steps:
echo 1. Add Twitter credentials to .env file:
echo    TWITTER_USERNAME=your_username
echo    TWITTER_EMAIL=your_email
echo    TWITTER_PASSWORD=your_password
echo.
echo 2. Add Reddit credentials to .env file:
echo    REDDIT_CLIENT_ID=your_client_id
echo    REDDIT_CLIENT_SECRET=your_client_secret
echo.
echo 3. Test with: python QueryEngine\tools\twitter_search.py
echo            or: python QueryEngine\tools\reddit_search.py
echo ========================================

pause
