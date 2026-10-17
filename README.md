# NexusAI — Smart AI Gateway with Semantic Caching 🚀

> Intelligent caching layer for LLM APIs that reduces costs by 80% and speeds up responses by 400x using machine learning.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 💡 What is this?

LLM APIs like OpenAI and Hugging Face charge per request and are slow (500-2000ms). **NexusAI fixes this** by caching responses intelligently.

Ask "What is the capital of France?" and later ask "What's France's capital city?" — it recognizes they're semantically similar and returns the cached answer instantly (5ms instead of 2 seconds).

### Key Features:
- 🧠 **Semantic matching** using ML embeddings
- ⚡ **5ms cache hits** vs 2000ms LLM calls  
- 💰 **80% cost savings** on repeated queries
- 📊 **Real-time monitoring** dashboard
- 🔑 **API key management** with quotas
- 🎨 **Beautiful web UI** for testing

---

## 🚀 Quick Start

### Option 1: Docker (Easiest)

```bash
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway
docker compose up
```

### Option 2: Local Python

```bash
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Open browser:** http://localhost:8000

**Default API Key:** `sk-nexus-dev-demo-key`

📖 **Detailed setup instructions:** See [SETUP.md](SETUP.md)

---

## 🎯 Try It Out

### 1. Use the Web Interface

1. Go to http://localhost:8000
2. Click "Playground" tab
3. Type: **"What is the capital of France?"**
4. Click Execute → See `CACHE MISS` (~12ms)
5. Try: **"What's France's capital city?"**
6. Click Execute → See `CACHE HIT` + 94% similarity! (~5ms)

### 2. Use the API

```bash
# First query (MISS)
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{"prompt": "What is the capital of France?", "provider": "mock"}'

# Similar query (HIT!)
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{"prompt": "What is France capital city?", "provider": "mock"}'
```

**API Documentation:** http://localhost:8000/docs

---

## 🏗️ How It Works

```
Your App → NexusAI Gateway → LLM API (OpenAI/HuggingFace)
               ↓
           Redis Cache
```

**Process:**
1. **Request arrives** → Check if it's a "live" query (weather, stocks)
2. **Generate embedding** → Convert text to 384-dimensional vector
3. **Search cache** → Find similar vectors (cosine similarity ≥ 92%)
4. **Cache HIT?** → Return instantly (5ms)
5. **Cache MISS?** → Call LLM, cache result, return (500-2000ms)

**Smart Features:**
- **Adaptive TTL:** Factual (24h), Technical (6h), General (1h)
- **Live Query Detection:** Weather, stocks bypass cache
- **LRU Eviction:** Removes least-used when full

---

## 📊 Features

### Core
✅ Semantic caching with ML  
✅ Multiple LLM providers (Mock, HuggingFace, OpenAI)  
✅ Smart TTL policies  
✅ Volatile query detection  
✅ Rate limiting (100 req/min)  
✅ LRU eviction  

### Monitoring & Admin
✅ Web dashboard (3 tabs)  
✅ Prometheus metrics  
✅ API key management  
✅ Daily quotas  
✅ Audit logging  
✅ Real-time statistics  

### Developer Tools
✅ Interactive API docs  
✅ Code examples (Python, JS, cURL)  
✅ 117 unit tests  
✅ Docker support  

---

## 📈 Performance & Cost Savings

| Scenario | Latency | Cost |
|----------|---------|------|
| Cache HIT | 5ms | $0 |
| Cache MISS | 500-2000ms | Normal LLM cost |
| 80% hit rate | ~100ms avg | 80% savings |

**Example:** 10,000 queries/day with 80% hit rate
- Without cache: $600/month
- With NexusAI: $120/month
- **Savings: $480/month** 💰

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11, FastAPI
- **Cache:** Redis 7
- **ML:** sentence-transformers (all-MiniLM-L6-v2)
- **Frontend:** Vanilla JavaScript
- **Deployment:** Docker
- **Testing:** pytest (117 tests)
- **Monitoring:** Prometheus

---

## 📚 Documentation

- **[SETUP.md](SETUP.md)** — Complete setup guide
- **[examples/](examples/)** — Code samples (Python, JS, cURL)
- **API Docs** — http://localhost:8000/docs

---

## 🧪 Testing

```bash
cd backend
pytest -v
```

**117 tests passing** ✓

---

## 🚢 Deployment

### Render.com (Free)
1. Sign up at render.com
2. Connect GitHub repo
3. Add Redis service
4. Deploy!

See [SETUP.md](SETUP.md) for detailed deployment instructions.

---

## 🎓 Project Context

Built as a 3rd-year college project exploring:
- Semantic search with transformers
- Caching strategies
- REST API design
- Production-ready development

**What I learned:**
- How ML embeddings work
- Redis as a vector database
- FastAPI framework
- Docker containerization
- Writing maintainable tests

---

## 📄 License

MIT License — use it for your projects!

---

## 👨‍💻 Author

Built by **Rashm** as a college project

**GitHub:** [BountyHunter2525](https://github.com/BountyHunter2525)

---

## 🙏 Acknowledgments

- sentence-transformers for ML models
- FastAPI for the framework
- Redis for caching
- OpenAI/HuggingFace for LLM APIs

---

**⭐ If this helped you, give it a star!**
