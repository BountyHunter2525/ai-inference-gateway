# NexusAI — Smart AI Gateway with Semantic Caching 🚀

> A lightweight AI inference gateway that caches similar queries to reduce costs and latency. Built as a college project to explore semantic similarity, caching strategies, and API design.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 💡 What is this?

Ever notice how LLM APIs like OpenAI charge per request, even if you ask the same question twice? **NexusAI fixes that.**

It sits between your app and the LLM, caching responses intelligently. Ask "What is the capital of France?" and later ask "What's France's capital city?" — it recognizes they're the same question and returns the cached answer instantly (5ms instead of 2 seconds).

### Key Features:
- 🧠 **Semantic matching** — understands similar questions using ML embeddings
- ⚡ **5ms cache hits** vs 2000ms LLM calls
- 💰 **Cost savings** — no repeated API charges
- 📊 **Live monitoring** — see hit rates, latency, and usage
- 🎨 **Web playground** — test queries in your browser
- 🔑 **API key management** — create and manage access keys

---

## 🚀 Quick Start

### Run with Docker (Easiest!)

```bash
# Clone and run
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway
docker compose up

# Open browser → http://localhost:8000
```

**Default API key:** `sk-nexus-dev-demo-key`

### Or run locally

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

---

## 🧪 Try It Out

### 1. Use the Web Playground
1. Open `http://localhost:8000`
2. Click "Playground" tab
3. Type: **"What is the capital of France?"**
4. Click Execute → see `CACHE MISS` (first time, ~200ms)
5. Try: **"What's France's capital city?"** → see `CACHE HIT` + similarity 94%! (~5ms)

### 2. Test with curl

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

---

## 🏗️ How It Works

```
Your App → NexusAI Gateway → LLM (OpenAI/HuggingFace)
               ↓
           Redis Cache
```

**Step-by-step:**
1. **Request arrives** → Check if it's a "live" query (weather, stock prices)
2. **Generate embedding** → Convert text to a 384-dimensional vector
3. **Search cache** → Find similar vectors (cosine similarity ≥ 0.92)
4. **Cache HIT?** → Return cached response instantly (5ms)
5. **Cache MISS?** → Call LLM, cache result, return (500-2000ms)

**Smart TTL (Cache Duration):**
- **Factual** queries ("capital of France") → 24 hours
- **Technical** queries ("how to use Docker") → 6 hours  
- **General** queries → 1 hour
- **Live** queries ("weather today") → bypass cache

---

## 📊 Features

### Core Functionality
✅ **Semantic Caching** — Similar questions get the same answer  
✅ **Multiple LLM Providers** — Mock (testing), HuggingFace (free), OpenAI  
✅ **Smart TTL** — Different cache durations for different query types  
✅ **Live Query Detection** — Bypasses cache for real-time data  
✅ **Rate Limiting** — Prevents abuse (100 req/min per key)

### Monitoring & Admin
✅ **Web Dashboard** — 3 tabs: Playground, Monitoring, Admin  
✅ **Prometheus Metrics** — Cache hit rates, latency percentiles  
✅ **API Key Management** — Create/revoke keys with daily quotas  
✅ **Audit Log** — Track all API usage and events

### Testing
✅ **117 Unit Tests** — Good test coverage  
✅ **CI Pipeline** — GitHub Actions for automated testing

---

## 🔧 Configuration

Create a `.env` file in the backend folder (optional):

```bash
# Redis (optional - uses in-memory fallback if not available)
REDIS_URL=redis://localhost:6379

# LLM Providers (only if you want real AI responses)
HUGGINGFACE_API_TOKEN=hf_your_token_here
OPENAI_API_KEY=sk-your_key_here

# Defaults work fine for testing
CACHE_MAX_ENTRIES=500
SIMILARITY_THRESHOLD=0.92
```

---

## 📱 Main API Endpoints

- `POST /api/v1/infer` — Execute inference with caching
- `GET /api/v1/health` — Health check
- `GET /api/v1/cache/stats` — View cache statistics
- `GET /api/v1/metrics` — Prometheus metrics
- `GET /docs` — Interactive API documentation

### Admin Endpoints (requires admin key)
- `GET /admin/keys` — List all API keys
- `POST /admin/keys` — Create new API key
- `GET /admin/audit` — View audit log

---

## 🧪 Testing

```bash
cd backend
pip install pytest pytest-asyncio
pytest -v

# Output: 117 tests passed ✓
```

Tests cover:
- Semantic similarity matching
- Cache hit/miss logic
- Query volatility detection  
- Rate limiting
- All API endpoints

---

## 🌐 Deploy It!

### Quick Deploy (Free Tier)

**Option 1: Render.com** (Recommended)
1. Create account at [render.com](https://render.com)
2. "New → Web Service" → Connect GitHub repo
3. Build command: `cd backend && pip install -r requirements.txt`
4. Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Redis service (also free on Render)
6. Set `REDIS_URL` environment variable
7. Deploy! 🎉

**Option 2: Railway.app**
1. Create account at [railway.app](https://railway.app)
2. "New Project" → Deploy from GitHub
3. Add Redis service
4. Set environment variables
5. Deploy!

**Option 3: DigitalOcean / AWS / GCP**
```bash
# SSH into your server
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway
docker compose up -d
```

---

## 📈 Performance & Cost Savings

| Scenario | Latency | Cost |
|----------|---------|------|
| Cache HIT | ~5ms | $0 |
| Cache MISS | 500-2000ms | Normal LLM cost |
| 80% hit rate | ~100ms avg | 80% cost reduction |

**Real example:**  
If you process 10,000 queries/day with an 80% hit rate:
- Without cache: 10,000 LLM calls = **$20/day**
- With NexusAI: 2,000 LLM calls = **$4/day**
- **Savings: $16/day = $480/month** 💰

---

## 🛠️ Tech Stack

**Backend:** Python, FastAPI, Redis  
**ML:** sentence-transformers (all-MiniLM-L6-v2)  
**Frontend:** Vanilla JavaScript, HTML/CSS  
**Deployment:** Docker, Docker Compose  
**Monitoring:** Prometheus metrics  
**Testing:** pytest (117 tests)

---

## 🎓 Project Context

This was built as a **3rd year college project** to explore:
- Semantic search using sentence-transformers
- Caching strategies (LRU eviction, TTL policies)
- REST API design with FastAPI
- Observability and monitoring
- Full-stack development

### What I Learned:
- How ML embeddings work and why they're useful for similarity
- Redis as a vector database
- Building production-ready APIs with proper authentication
- Docker containerization and deployment
- Writing maintainable unit tests
- Prometheus metrics and monitoring

---

## 📝 Project Structure

```
NexusAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── api/v1/              # API endpoints
│   │   ├── services/            # Core logic (cache, embeddings, etc)
│   │   └── schemas/             # Request/response models
│   ├── tests/                   # Unit tests (117 tests)
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Web playground UI
│   ├── app.js                   # JavaScript logic
│   └── style.css                # Styling
├── docker-compose.yml           # Docker setup
└── README.md
```

---

## 🤝 Contributing

This is a college project but feel free to:
- Open issues for bugs
- Suggest improvements
- Fork and modify for your own projects

---

## 📄 License

MIT License — Use it for your projects, assignments, hackathons, whatever!

---

## 👨‍💻 Author

Built by **Rashm** as a 3rd year college project exploring AI caching and API design.

**GitHub:** [BountyHunter2525](https://github.com/BountyHunter2525)

---

## 🙏 Acknowledgments

- sentence-transformers for semantic embeddings
- FastAPI for making Python APIs easy
- Redis for being an awesome cache
- OpenAI/HuggingFace for LLM APIs

---

## 📚 Useful Resources

If you want to learn more about the concepts used:
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Redis Caching Guide](https://redis.io/docs/manual/client-side-caching/)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)

---

**⭐ If this helped you with your project, consider giving it a star!**
