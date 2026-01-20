@echo off
echo Starting Email Scraper...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

echo Launching GUI...
python gui.py

if errorlevel 1 (
    echo Error: Failed to launch application.
    pause
    exit /b 1
)
