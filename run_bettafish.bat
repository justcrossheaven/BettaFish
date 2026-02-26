@echo off
echo Starting BettaFish...
echo.

REM Activate conda environment and run the app
call "C:\Users\John Jia\miniconda3\Scripts\activate.bat" bettafish
python app.py

pause
