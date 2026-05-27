@echo off
chcp 65001 >nul
title GTarcade PK Generator

echo ========================================
echo   GTarcade PK Activity Generator
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create venv if not exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate venv and install deps
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo.
echo ========================================
echo   Starting server...
echo   Access locally:  http://localhost:8501
echo   Access from LAN: http://YOUR_IP:8501
echo ========================================
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Start Streamlit on 0.0.0.0 so LAN devices can access
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

pause
