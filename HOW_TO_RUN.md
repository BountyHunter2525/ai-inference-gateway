# 🚀 How to Run NexusAI

**Super simple guide - Choose your method below!**

---

## ⚡ Method 1: Windows Double-Click (EASIEST!)

### Step 1: Find the file
Look for **`start_local.bat`** in your NexusAI folder

### Step 2: Double-click it
Just double-click the file!

### Step 3: Wait
First time: ~3 minutes (installs everything)  
After that: ~5 seconds

### Step 4: Open browser
Go to: **http://localhost:8000**

**Done!** 🎉

---

## 🐳 Method 2: Docker (If you have it)

```bash
docker compose up
```

Then open: http://localhost:8000

---

## 💻 Method 3: Manual (If batch file doesn't work)

```powershell
# 1. Open PowerShell in project folder
cd NexusAI\backend

# 2. Create virtual environment (first time only)
python -m venv venv

# 3. Activate it
.\venv\Scripts\activate

# 4. Install dependencies (first time only)
pip install -r requirements.txt

# 5. Start server
python -m uvicorn app.main:app --reload
```

Then open: http://localhost:8000

---

## ✅ How to Know It's Working

You should see this in the terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Then in your browser at http://localhost:8000 you'll see:
- Beautiful dark UI
- "NexusAI" logo
- Three tabs: Playground, Monitoring, Admin

---

## 🎯 First Test

1. **Click "Playground" tab** (should be already selected)
2. **Click the blue button:** "Capital of France"
3. **Click "Execute Inference"**
4. **See the result** appear below!

If you see a response, **IT'S WORKING!** ✨

---

## 🛑 How to Stop It

Press **Ctrl+C** in the terminal window

Or just close the terminal

---

## 🐛 Common Issues

### Issue: "python is not recognized"
**Fix:** Python not installed or not in PATH
- Install Python from python.org
- Or check PATH in Environment Variables

### Issue: "Port 8000 already in use"
**Fix:** Something else is using port 8000
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <number> /F

# Or use different port
python -m uvicorn app.main:app --reload --port 8001
```

### Issue: "Module not found"
**Fix:** Dependencies not installed
```powershell
cd backend
pip install -r requirements.txt
```

### Issue: Nothing happens when I double-click
**Fix:** Try PowerShell method or Manual method above

---

## 📖 What to Do After It's Running

### Try the Demo
1. Go to http://localhost:8000
2. Play with different queries
3. Check the Monitoring tab
4. Try the Admin panel

### Run Examples
```powershell
# Python example
python examples\python_client.py

# Open JavaScript example in browser
start examples\javascript_client.html
```

### Read the Guides
- **USAGE_GUIDE.md** — How to use everything
- **PRESENTATION.md** — How to present it
- **PROJECT_REPORT.md** — For your report

---

## 🎤 For Your Presentation

**Before your demo:**
1. Run `start_local.bat` 
2. Wait for "Application startup complete"
3. Open browser to http://localhost:8000
4. Test one query to make sure it works
5. **Leave it running** during presentation

**During demo:**
- Show the UI
- Execute queries
- Point out the speed difference (HIT vs MISS)
- Show monitoring tab
- Show admin panel

**Pro tip:** Practice the demo flow 2-3 times before presenting!

---

## ⏱️ Time Estimates

| Task | First Time | After That |
|------|-----------|------------|
| Install dependencies | ~3 min | — |
| Start server | ~10 sec | ~5 sec |
| Load web page | ~1 sec | ~1 sec |
| Execute query | ~10-50ms | ~5-10ms |
| **Total to demo ready** | **~4 min** | **~10 sec** |

---

## 🆘 Still Need Help?

1. **Check WINDOWS_SETUP.md** — More detailed Windows guide
2. **Check error message** — Google it!
3. **Check Python version** — `python --version` (need 3.11+)
4. **Try manual method** — More control over steps

---

## ✨ Quick Reference

**Start:** Double-click `start_local.bat`  
**Stop:** Ctrl+C  
**URL:** http://localhost:8000  
**API Key:** `sk-nexus-dev-demo-key`  
**Docs:** http://localhost:8000/docs  

---

**That's it! You're ready to go! 🚀**

Any issues? Check **WINDOWS_SETUP.md** for troubleshooting.
