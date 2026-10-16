@echo off
REM ===================================================================
REM   NexusAI - DOUBLE CLICK THIS TO START THE SERVER
REM ===================================================================

echo.
echo ========================================
echo   Starting NexusAI Gateway
echo ========================================
echo.

cd backend

echo [1/2] Checking dependencies...
C:\Users\rashm\AppData\Local\Programs\Python\Python311\python.exe -m pip install -q uvicorn fastapi redis pydantic sentence-transformers torch numpy prometheus-client 2>nul

echo [2/2] Starting server...
echo.
echo ========================================
echo   SERVER IS STARTING!
echo ========================================
echo.
echo   Open your browser to:
echo   http://localhost:8000
echo.
echo   API Key: sk-nexus-dev-demo-key
echo.
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

C:\Users\rashm\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
