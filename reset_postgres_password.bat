@echo off
REM Reset PostgreSQL postgres user password
echo Resetting PostgreSQL password...
echo.

REM Add PostgreSQL bin to PATH temporarily
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

REM Set new password (change "newpassword" to whatever you want)
set PGPASSWORD=postgres
psql -U postgres -p 5433 -c "ALTER USER postgres WITH PASSWORD 'postgres';"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Password successfully reset to: postgres
    echo.
    echo You can now connect with:
    echo   Username: postgres
    echo   Password: postgres
    echo   Port: 5433
) else (
    echo.
    echo ✗ Failed to reset password. The current password might not be 'postgres'.
    echo Try running pgAdmin 4 and connect with different passwords.
)

pause
