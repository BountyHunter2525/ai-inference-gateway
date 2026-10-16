# Windows Setup Guide (No Docker Required)

Quick guide to run NexusAI on Windows without Docker.

---

## 🎯 Quick Start (Easiest)

### Option 1: Double-Click Method

1. **Find the file:** `start_local.bat` in the project folder
2. **Double-click it** to start the server
3. **Wait** for dependencies to install (first time only, ~2-3 minutes)
4. **Open browser** to http://localhost:8000

**That's it!** ✨

---

### Option 2: PowerShell Method

```powershell
# Right-click start_local.ps1 → Run with PowerShell
# Or in PowerShell:
.\start_local.ps1
```

---

### Option 3: Manual Method

```powershell
# 1. Go to backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start server
python -m uvicorn app.main:app --reload
```

Then open: http://localhost:8000

---

## ✅ What You Need

**Required:**
- ✅ Python 3.11+ (you have 3.14 ✓)
- ✅ pip (comes with Python)
- ✅ Internet connection (first time only)

**Optional:**
- Redis (app works without it using in-memory cache)

---

## 🐛 Troubleshooting

### "python is not recognized"

**Fix:** Add Python to PATH
1. Search "Environment Variables" in Windows
2. Edit PATH variable
3. Add: `C:\Users\rashm\AppData\Local\Programs\Python\Python314`
4. Restart terminal

### "Port 8000 is already in use"

**Fix:** Kill the process using port 8000
```powershell
# Find process
netstat -ano | findstr :8000

# Kill it (replace PID with the number you see)
taskkill /PID <PID> /F
```

Or use a different port:
```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### "ModuleNotFoundError"

**Fix:** Install dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### "Execution policy error" (PowerShell script)

**Fix:** Allow script execution
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then run the script again.

---

## 📦 Installing Redis (Optional)

Redis makes caching persistent across restarts.

### Method 1: Memurai (Redis for Windows)

1. Download: https://www.memurai.com/
2. Install (free version)
3. Start Memurai service
4. Restart NexusAI

### Method 2: WSL (Windows Subsystem for Linux)

```powershell
# In WSL terminal:
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

### Skip Redis?

**No problem!** The app automatically uses in-memory cache if Redis isn't available.

---

## 🔧 First Time Setup

When you first run `start_local.bat`:

1. **Creates virtual environment** (~30 seconds)
2. **Installs dependencies** (~2-3 minutes)
   - FastAPI, Redis, ML models
   - Downloads sentence-transformers model (~90 MB)
3. **Starts server** (~5 seconds)

**Total:** ~3-4 minutes first time  
**After that:** ~5 seconds to start!

---

## ✨ Verify It's Working

### 1. Check health

Open browser to: http://localhost:8000/api/v1/health

Should see:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "backend_storage": "MEMORY",
  "embedder_ready": true
}
```

### 2. Try the playground

Go to: http://localhost:8000

You should see the NexusAI interface!

### 3. Test an API call

```powershell
# In a new PowerShell window:
curl -X POST http://localhost:8000/api/v1/infer `
  -H "Content-Type: application/json" `
  -H "X-API-Key: sk-nexus-dev-demo-key" `
  -d '{"prompt":"What is the capital of France?","provider":"mock"}'
```

---

## 🎯 What Next?

Once it's running:

1. ✅ **Test it:** Try the examples in `examples/`
2. 📖 **Learn it:** Read `USAGE_GUIDE.md`
3. 🎤 **Present it:** Use `PRESENTATION.md`
4. 🚀 **Deploy it:** Read `DEPLOYMENT.md`

---

## 💡 Tips

**Stop the server:**
- Press `Ctrl+C` in the terminal

**Restart the server:**
- Just run `start_local.bat` again

**Update dependencies:**
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

**Run tests:**
```powershell
cd backend
.\venv\Scripts\activate
pytest -v
```

---

## 📊 Performance Notes

**Without Redis:**
- ✅ Cache works great
- ❌ Cache cleared on restart
- ⚡ Still fast (5ms cache hits)

**With Redis:**
- ✅ Cache persists across restarts
- ✅ Better for production
- ✅ Supports distributed deployment

**For demos/development:** In-memory is fine!  
**For production:** Use Redis

---

## 🎓 For Your Demo

Just use `start_local.bat`:

1. **Before demo:** Run `start_local.bat` to start server
2. **During demo:** Show the web interface
3. **After demo:** Press Ctrl+C to stop

**Pro tip:** Start it 5 minutes before your presentation to make sure everything's loaded!

---

## 🆘 Still Having Issues?

1. **Check Python version:** `python --version` (need 3.11+)
2. **Check pip works:** `pip --version`
3. **Try manual method** (Option 3 above)
4. **Check logs** for error messages
5. **Google the error** (usually Python/pip issues)

---

## ✅ Quick Checklist

Before presenting:

- [ ] Python installed (3.11+)
- [ ] Can run `start_local.bat`
- [ ] Browser opens to localhost:8000
- [ ] Can execute a test query
- [ ] Checked all 3 tabs (Playground, Monitoring, Admin)

---

**You're ready to go! 🚀**

Just double-click `start_local.bat` and you're good!
