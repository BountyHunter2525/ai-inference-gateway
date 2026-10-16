@echo off
REM NexusAI Local Startup Script (Windows)
REM Double-click this file to start the project

echo ========================================
echo   NexusAI Gateway - Local Mode
echo ========================================
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Dependencies installed!
echo.

REM Start server
echo ========================================
echo   Server Starting!
echo ========================================
echo.
echo   URL: http://localhost:8000
echo   API Key: sk-nexus-dev-demo-key
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
