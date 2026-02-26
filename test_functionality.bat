@echo off
echo Running Twitter and Reddit Functionality Tests...
echo.

REM Activate conda environment and run functional tests
call "C:\Users\John Jia\miniconda3\Scripts\activate.bat" bettafish

python test_platform_functionality.py

pause
