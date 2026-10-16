# NexusAI Local Startup Script (Windows)
# Run this to start the project without Docker

Write-Host "🚀 Starting NexusAI Gateway (Local Mode)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend
Set-Location backend

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created!" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📥 Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check for Redis (optional)
Write-Host "🔍 Checking for Redis..." -ForegroundColor Yellow
$redisRunning = $false
try {
    $null = Test-NetConnection -ComputerName localhost -Port 6379 -ErrorAction Stop
    $redisRunning = $true
    Write-Host "✅ Redis is running on localhost:6379" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Redis not found - using in-memory cache fallback" -ForegroundColor Yellow
}
Write-Host ""

# Start the server
Write-Host "🌟 Starting NexusAI Gateway..." -ForegroundColor Cyan
Write-Host ""
Write-Host "   URL: http://localhost:8000" -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "   API Key: sk-nexus-dev-demo-key" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
