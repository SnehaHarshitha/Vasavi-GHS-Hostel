@echo off
title GHS Hostel Website Startup
echo ===================================================
echo     Starting GHS Hostel Management System...
echo ===================================================
cd /d "%~dp0"

echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9 or higher and add it to PATH.
    pause
    exit /b 1
)

echo Starting website launcher...
python run.py
pause
