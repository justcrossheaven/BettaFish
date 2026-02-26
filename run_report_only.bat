@echo off
echo ============================================
echo    Report Engine Only - Conda Environment
echo ============================================
echo.

REM Activate conda environment
call conda activate bettafish

REM Check if activation succeeded
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment 'bettafish'
    echo Please ensure the environment exists: conda env list
    pause
    exit /b 1
)

echo Conda environment 'bettafish' activated successfully
echo.

REM Run the report engine only script
echo Running report_engine_only.py...
echo.
python report_engine_only.py --verbose

echo.
echo ============================================
echo    Report Generation Complete
echo ============================================
pause
