# Installing Redis on Windows

## Option 1: Memurai (Recommended for Windows)

1. **Download Memurai** (Redis for Windows):
   - Visit: https://www.memurai.com/get-memurai
   - Download the free version
   - Install it (next, next, finish)

2. **Start Memurai:**
   - It runs as a Windows service automatically
   - Default port: 6379

3. **Verify it's running:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 6379
   ```

## Option 2: WSL2 + Redis (Alternative)

If you have WSL2 installed:

```bash
# In WSL2 terminal:
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

## Option 3: Docker Redis

If you have Docker:

```powershell
docker run -d -p 6379:6379 --name nexusai-redis redis:7-alpine
```

## Verify Redis Works

Open PowerShell and run:

```powershell
# Test connection
$redis = New-Object System.Net.Sockets.TcpClient
$redis.Connect("localhost", 6379)
if ($redis.Connected) {
    Write-Host "✅ Redis is running!" -ForegroundColor Green
} else {
    Write-Host "❌ Redis is not running" -ForegroundColor Red
}
$redis.Close()
```

## After Installing

Restart your NexusAI server and you should see:
```
✅ Connected to Redis at redis://localhost:6379
```

Instead of:
```
⚠️ Using In-Memory cache fallback
```

**Benefits with Redis:**
- Cache persists across server restarts
- Better performance
- Production-ready
- Can scale to multiple servers
