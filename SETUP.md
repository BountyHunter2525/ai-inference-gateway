# NexusAI Setup Guide

Complete guide to get NexusAI running on your machine.

---

## 📋 Prerequisites

- **Python 3.11+** (Download from [python.org](https://www.python.org/downloads/))
- **Git** (Download from [git-scm.com](https://git-scm.com/))
- **Redis** (Optional but recommended - see Redis Setup below)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Server

```bash
# Option 1: Docker (if you have it)
docker compose up

# Option 2: Direct Python
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open Your Browser

Navigate to: **http://localhostost:8000**

**Default Credentials:**
- **API Key:** `sk-nexus-dev-demo-key`
- **Admin Key:** `sk-nexus-admin-master-key`

---

## ⚙️ Configuration

### Basic Setup (.env file)

Create `backend/.env`:

```bash
# Redis (optional - uses in-memory if not available)
REDIS_URL=redis://localhost:6379

# API Keys
VALID_API_KEYS=sk-nexus-dev-demo-key
ADMIN_API_KEY=sk-nexus-admin-master-key

# Application
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Cache Settings
CACHE_MAX_ENTRIES=500
SIMILARITY_THRESHOLD=0.92

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

---

## 🗄️ Redis Setup (Recommended)

Redis makes caching persistent across server restarts.

### Windows

1. **Download Memurai** (Redis for Windows)
   - Visit: https://www.memurai.com/get-memurai
   - Download free version
   - Install and run

2. **Verify Redis is running:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 6379
   ```

### Linux/Mac

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping
# Should return: PONG
```

### Docker (All Platforms)

```bash
docker run -d -p 6379:6379 --name nexusai-redis redis:7-alpine
```

---

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest -v
```

**Expected:** 117 tests passing ✓

---

## 🎯 Using the Application

### Web Interface

1. **Playground Tab:**
   - Test queries
   - See cache HIT/MISS in real-time
   - Try sample queries

2. **Monitoring Tab:**
   - View performance metrics
   - Cache hit rates
   - Latency statistics

3. **Admin Tab:**
   - Manage API keys
   - View audit logs
   - Monitor quotas

### API Usage

**Execute Inference:**
```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "mock"
  }'
```

**Check Health:**
```bash
curl http://localhost:8000/api/v1/health
```

**View Metrics:**
```bash
curl http://localhost:8000/api/v1/metrics
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 Troubleshooting

### Issue: "Module not found"

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find and kill process on port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port:
python -m uvicorn app.main:app --port 8001
```

### Issue: "Redis connection failed"

**Solution:**
- App works without Redis (uses in-memory cache)
- To use Redis, follow Redis Setup section above
- Verify Redis is running: `redis-cli ping`

### Issue: UI not loading properly

**Solution:**
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Check console for errors
- Verify static files are being served

---

## 📦 Project Structure

```
NexusAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── schemas/        # Data models
│   ├── tests/              # 117 tests
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── examples/               # Code samples
│   ├── python_client.py
│   ├── javascript_client.html
│   └── curl_examples.sh
├── docker-compose.yml
└── README.md
```

---

## 🚢 Deployment

### Production Deployment (Render.com)

1. **Sign up at render.com**

2. **Create Redis service:**
   - New + → Redis
   - Free tier is fine
   - Copy Internal Redis URL

3. **Create Web Service:**
   - New + → Web Service
   - Connect your GitHub repo
   - Build command: `cd backend && pip install -r requirements.txt`
   - Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Set environment variables:**
   ```
   REDIS_URL=<your redis url>
   DEBUG=False
   ADMIN_API_KEY=<change this>
   VALID_API_KEYS=<change this>
   ```

5. **Deploy!**

### Other Platforms

- **Railway.app:** Similar to Render
- **Heroku:** Add Redis addon
- **AWS/GCP:** Use container services
- **VPS:** Use Docker Compose

---

## 🔒 Security Notes

**Before Production:**
- ✅ Change default API keys
- ✅ Set `DEBUG=False`
- ✅ Configure CORS properly
- ✅ Enable HTTPS
- ✅ Use strong passwords
- ✅ Regular security updates

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **GitHub:** https://github.com/BountyHunter2525/ai-inference-gateway
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Redis Docs:** https://redis.io/docs

---

## 💡 Tips

- **First run** takes longer (downloads ML model ~90MB)
- **Redis is optional** but recommended for production
- **Tests** ensure everything works correctly
- **Examples folder** has working code samples
- **Check logs** if something goes wrong

---

## ✅ Quick Checklist

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Redis running (optional)
- [ ] Server starts without errors
- [ ] Browser opens to http://localhost:8000
- [ ] Can execute test query
- [ ] All 3 tabs working (Playground, Monitoring, Admin)

---

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Review error messages carefully
3. Verify all prerequisites are met
4. Check GitHub issues
5. Review API documentation

---

**That's it! You should now have NexusAI running successfully.** 🚀
