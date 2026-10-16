# NexusAI — Intelligent AI Inference Gateway & Semantic Cache

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0%2B-dc382d.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**NexusAI** is a high-performance **AI Inference Gateway** designed to act as a smart proxy between user applications and Large Language Model (LLM) providers (Hugging Face, OpenAI, OpenRouter, or local engines). 

It features **Semantic Vector Caching**, **Real-Time Volatility Classification**, **Sliding-Window Rate Limiting**, and an interactive **Developer Playground**.

---

## 📌 The Problem NexusAI Solves

Standard API calls to LLM providers are expensive, slow (often 500ms–3000ms), and repetitive:
* Up to **80% of customer queries** in FAQs, customer support, and document querying are semantically identical or near-identical.
* **Exact match caching fails** when a user asks *"What is the capital of France?"* vs. *"What is France's capital city?"*.
* **Naive semantic caching returns stale answers** when queries involve dynamic data (e.g. *"What is the weather today?"* or *"Latest Bitcoin price"*).

### NexusAI's 3-Layer Solution:
1. **Semantic Vector Similarity ($\ge 0.92$)**: Converts prompts to high-dimensional embeddings and calculates cosine similarity against stored vectors in Redis. Cache hits return previously computed AI responses in **< 10ms**.
2. **Dynamic Volatility Classifier**: Automatically detects real-time intents (`weather`, `price`, `latest news`, `now`) and routes directly to the LLM, bypassing cache.
3. **Automatic TTL (Time-To-Live)**: Stored responses expire gracefully according to volatility windows.

---

## 🏗️ Architecture

```
User / Web Playground / Client Apps
                 │
                 ▼  (POST /api/v1/infer with API Key)
      ┌──────────────────────────────────────────────┐
      │               NexusAI Gateway                │
      │                                              │
      │  1. Auth & Sliding Window Rate Limiter       │
      │  2. Volatility Query Classifier              │
      │  3. Sentence Embedding Engine                │
      └───────┬──────────────────────────────┬───────┘
              │                              │
     (Semantic Match >= 0.92)         (Cache MISS / Real-time)
              │                              │
              ▼                              ▼
      ┌───────────────┐              ┌──────────────────────────┐
      │  Redis Cache  │              │    LLM Model Providers   │
      │ (Vectors+TTL) │              │  - Hugging Face API      │
      │  Latency <10ms│              │  - OpenAI / OpenRouter   │
      └───────────────┘              │  - Nexus Mock Engine     │
                                     └─────────────┬────────────┘
                                                   │
                                                   ▼
                                        Save Vector + Response
                                            into Redis (TTL)
```

---

## 🚀 Quick Start

### Option A: Run with Docker Compose (Recommended)

Requires Docker & Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-username/NexusAI.git
cd NexusAI

# Launch Gateway and Redis
docker compose up --build
```
The gateway and interactive playground will be live at `http://localhost:8000`.

---

### Option B: Run Locally with Python

Works out of the box even without Redis installed (automatically uses In-Memory vector store fallback):

```bash
cd NexusAI/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the gateway
python -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser to access the Developer Playground!

---

## 🧪 Testing the Semantic Cache

1. Open `http://localhost:8000`
2. **First Query (Cache MISS)**:
   - Click the sample: `What is the capital of France?`
   - Click **Execute Inference**.
   - Notice the badge says `CACHE MISS`, latency is ~200ms, and the entry appears in the **Active Cached Memory Entries** table.
3. **Second Query (Semantic Cache HIT)**:
   - Click the sample: `What is France's capital city?`
   - Click **Execute Inference**.
   - Notice the badge turns green: `CACHE HIT`, latency drops to **~5ms**, and the similarity score indicates a match!
4. **Third Query (Volatile Cache Bypass)**:
   - Click the sample: `What is the weather today in Tokyo?`
   - Notice the gateway detects temporal volatility and tags it with `REALTIME BYPASS`, ensuring fresh data is always fetched.

---

## 📡 API Reference

### 1. Execute Inference
`POST /api/v1/infer`

**Headers:**
* `X-API-Key: sk-nexus-dev-demo-key`
* `Content-Type: application/json`

**Request Body:**
```json
{
  "prompt": "What is the capital of France?",
  "provider": "mock",
  "bypass_cache": false,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "prompt": "What is the capital of France?",
  "response": "The capital of France is Paris. It is renowned for its art, fashion, gastronomy, and culture.",
  "model": "nexus-mock-v1",
  "provider": "mock",
  "cache_hit": true,
  "similarity_score": 0.965,
  "latency_ms": 4.82,
  "tokens_used": 28,
  "bypassed_due_to_volatility": false,
  "timestamp": 1729094000.12
}
```

### 2. Cache Telemetry & Stats
`GET /api/v1/cache/stats`

Returns active cache size, hit/miss ratios, and entry lists with remaining TTL.

### 3. Flush Cache
`DELETE /api/v1/cache/clear`

Purges all cached vectors and resets telemetry counters.

### 4. Health Check
`GET /api/v1/health`

---

## 📂 Project Structure

```
NexusAI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app & static playground mount
│   │   ├── config.py                # Environment configurations
│   │   ├── api/
│   │   │   ├── deps.py              # API Key auth & sliding rate limit
│   │   │   └── v1/
│   │   │       ├── inference.py     # POST /api/v1/infer
│   │   │       ├── cache_admin.py   # GET/DELETE /api/v1/cache
│   │   │       └── health.py        # GET /api/v1/health
│   │   ├── services/
│   │   │   ├── semantic_cache.py    # Vector similarity cache (Cosine >= 0.92)
│   │   │   ├── query_classifier.py  # Volatility / real-time query detection
│   │   │   ├── rate_limiter.py      # Redis sliding window counter
│   │   │   ├── embedder.py          # Sentence-transformers embedder + fallback
│   │   │   └── llm_provider.py      # HuggingFace, OpenAI, and Mock providers
│   │   └── schemas/
│   │       └── inference.py         # Request & Response Pydantic models
│   ├── tests/
│   │   └── test_cache.py            # Automated test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html                   # Developer playground UI
│   ├── style.css                    # Glassmorphism dark mode UI
│   └── app.js                       # Telemetry polling & interactive runner
├── docker-compose.yml               # Gateway + Redis container orchestration
├── .env.example
├── .gitignore
└── README.md
```

---

## 📄 License
MIT License. Built for scalable, low-latency AI inference.
