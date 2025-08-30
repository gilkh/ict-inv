@echo off
title ICT Inventory - Public Access
color 0A

echo.
echo ============================================================
echo    ICT Inventory - Public Access Setup
echo ============================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Checking if virtual environment exists...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating requirements...
pip install flask pymongo pandas openpyxl requests

echo.
echo ============================================================
echo    Starting ICT Inventory with Public Access
echo ============================================================
echo.

echo Starting the application...
python app.py

pause 