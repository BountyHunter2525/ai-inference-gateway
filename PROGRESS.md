# NexusAI — Project Progress

> **Repository:** [BountyHunter2525/ai-inference-gateway](https://github.com/BountyHunter2525/ai-inference-gateway)  
> **Stack:** Python 3.11+ · FastAPI · Redis · sentence-transformers · Prometheus · Vanilla JS  
> **Last updated:** October 2026

---

## Commit History

| SHA | Message | Date |
|---|---|---|
| `ccc5b13` | feat: advanced cache management with adaptive TTL, LRU eviction, and cache warming | Oct 2026 |
| `f349420` | test: expand test suite to 117 tests and fix CI pipeline | Oct 2026 |
| `d376f59` | feat: add ML embeddings and Prometheus observability | Oct 2026 |
| `d377433` | ci: add GitHub Actions workflow with tests, lint, and boot check | Oct 2026 |
| `dd231c0` | test: unit tests for all core services (4/4 passing) | Oct 2026 |
| `b49c3d2` | feat(frontend): glassmorphism developer playground UI | Oct 2026 |
| `9fc4a92` | feat(api): FastAPI routes, auth middleware, and application entrypoint | Oct 2026 |
| `7734745` | feat(services): semantic cache, embedder, query classifier, rate limiter, LLM providers | Oct 2026 |
| `61474cd` | feat(backend): project structure, config, and Pydantic schemas | Oct 2026 |
| `2c14985` | chore: initial project scaffold | Oct 2026 |

---

## Completed Options

### ✅ Core Foundation
The base gateway was built first — all features below build on top of it.

| Component | What was built |
|---|---|
| FastAPI app | `POST /infer`, `GET /health`, `GET /cache/stats`, `DELETE /cache/clear`, CORS middleware |
| Semantic cache | Redis backend with in-memory fallback, cosine similarity lookup, TTL storage |
| Embedder | sentence-transformers `all-MiniLM-L6-v2` with lightweight hash-based fallback |
| Query classifier | Regex-based volatility detector — bypasses cache for weather/prices/live events |
| Rate limiter | Sliding-window counter (Redis + in-memory) with configurable max requests/window |
| LLM providers | Mock (instant), Hugging Face API, OpenAI / OpenRouter — unified interface |
| Auth | `X-API-Key` header or `?api_key=` query param, comma-separated key list |
| Docker | `docker-compose.yml` — gateway + Redis, health-checked, frontend volume-mounted |
| Frontend playground | Glassmorphism dark-mode UI — inference form, cache telemetry panel, sample queries |

---

### ✅ Option 1 — ML Embeddings (`sentence-transformers`)
**Commit:** `d376f59`

- Upgraded `embedder.py` to use `all-MiniLM-L6-v2` (384-dim, 1B+ training pairs)
- Thread-safe lazy loading with a background daemon warmup thread — zero startup blocking
- `embed_batch()` for bulk encoding at 32 items/batch
- Graceful fallback to deterministic hash embedder when torch is unavailable
- Added `sentence-transformers>=3.3.0` and `torch>=2.2.0` to `requirements.txt`

---

### ✅ Option 2 — Prometheus Observability + Monitoring Dashboard
**Commit:** `d376f59`

**Backend:**
- `services/metrics.py` — single Prometheus registry with counters, histograms, and gauges covering inference, cache, embedder, rate limiter, and volatility classifier
- `GET /api/v1/metrics` — standard Prometheus text scrape endpoint (no auth required)
- Every inference path (`hit` / `miss` / `volatile_bypass` / `error`) instrumented
- Embed latency recorded per backend label (`sentence_transformers` / `hash_fallback`)

**Frontend — Monitoring Tab:**
- Embedder backend KPIs (active backend, total encodes, p50 latency)
- Gateway health KPIs (cache backend, total requests, error count)
- Throughput cards: hits, misses, volatile bypasses, cumulative token usage
- Latency percentile panels (p50 / p90 / p99) with animated bar charts for hit, miss, and embed paths
- Cosine similarity score histogram
- Rate limiter pass-rate fill bar
- Raw Prometheus output panel with live filter input
- Auto-refreshes every 6 s when monitoring tab is active

---

### ✅ Option 3 — Advanced Cache Management
**Commit:** `ccc5b13`

**Adaptive TTL Engine (`cache_ttl_policy.py`):**
| Tier | TTL | Trigger keywords |
|---|---|---|
| Factual | 24 h | capital, definition, history, formula, geography, founder… |
| Technical | 6 h | algorithm, API, docker, kubernetes, code, cloud, Python… |
| General | 1 h | everything else |

**LRU Eviction:**
- `CACHE_MAX_ENTRIES = 500` (configurable)
- Every `CachedItem` tracks `access_count` and `last_accessed`
- `_maybe_evict()` removes the least-recently-accessed entry before storing a new one

**Cache Warming (`cache_warming.py`):**
- `startup_warmup()` fires on FastAPI lifespan start — pre-loads 10 seed queries
- Deduplication: skips prompts with an existing similar entry (cosine ≥ threshold)
- Batch-embeds all prompts in one model call for efficiency

**3 New Admin Endpoints:**
| Endpoint | Purpose |
|---|---|
| `POST /api/v1/cache/warm` | Trigger warm-up with optional custom query list |
| `DELETE /api/v1/cache/evict/{id}` | Remove a single entry by UUID |
| `GET /api/v1/cache/inspect/{id}` | Full entry detail including response, access count, remaining TTL |

**6 New Prometheus Metrics:**
`CACHE_EVICTIONS_TOTAL`, `CACHE_WARMUP_ENTRIES_TOTAL`, `CACHE_WARMUP_RUNS_TOTAL`, `CACHE_TTL_ASSIGNED` (histogram), `CACHE_TTL_CATEGORY_TOTAL` (per-category counter), `CACHE_ACCESS_COUNT` (histogram)

**Frontend additions:**
- Advanced Cache Management row: evictions, warm-up entries, capacity %, one-click warm-up button
- TTL category breakdown panel with animated percentage bars
- Top-5 accessed entries panel ranked by hit count
- Playground entry list shows TTL category dot and access count
- CACHE MISS badge shows assigned category (e.g. `CACHE MISS · FACTUAL TTL`)

---

### ✅ Option 6 — Comprehensive Test Suite + CI Pipeline Fix
**Commit:** `f349420`

**117 tests across 4 modules:**

| File | Tests | Coverage |
|---|---|---|
| `test_cache.py` | 43 | Classifier (15 parametrized volatile/non-volatile), hash embedder, cosine similarity, EmbedderService (batch, properties), SemanticCacheManager (TTL, stats, clear), rate limiter |
| `test_inference_api.py` | 39 | Health, auth (401/403), `/infer` miss→hit→volatile cycle, all response headers, mock LLM branches, cache admin CRUD, `/metrics` scrape |
| `test_metrics.py` | 22 | Module import, `prometheus_output`, 11 counter increments by label, 4 histogram observations, 3 gauge operations |
| `test_llm_provider.py` | 28 | Mock all branches, HuggingFace (HTTP 200 list/dict, error), OpenAI (usage field, no-key fallback, error), LLMService routing |

**CI pipeline fixes:**
- CPU-only torch wheel (`TORCH_INDEX_URL`) — saves ~2.4 GB per run
- `actions/cache@v4` for sentence-transformers model (~90 MB, keyed by model + OS)
- `asyncio_mode = auto` in `pyproject.toml` for pytest-asyncio
- `fail-fast: false` — both Python 3.11 and 3.12 always report
- Boot-check job verifies 3 key `nexusai_*` metric names in `/api/v1/metrics`

---

## Remaining Options

### Option 4 — Enterprise Features 🏢
**Complexity:** High | **Value:** Production deployment

- [ ] JWT / OAuth2 token authentication alongside the current API key system
- [ ] Per-key usage quotas and billing counters (tokens used, requests per day)
- [ ] Multi-tenancy: isolated cache namespaces per API key or tenant ID
- [ ] Admin dashboard UI for API key management (create, revoke, view usage)
- [ ] Structured audit logging (who called what, when, with what result)
- [ ] Role-based access control (read-only keys, admin keys, etc.)

---

### Option 5 — Advanced AI Features 🤖
**Complexity:** Medium | **Value:** Highest UX impact

- [ ] **Response streaming** — Server-Sent Events (SSE) from `/infer/stream` so tokens render live in the browser instead of waiting for the full response
- [ ] Multi-model routing — auto-select cheapest/fastest provider based on prompt length and query category
- [ ] Response quality scoring — compare cached vs fresh response and flag degraded hits
- [ ] Prompt optimization suggestions — detect common rephrasing patterns and suggest canonical forms
- [ ] Context-aware caching — consider prior conversation turns, not just the current prompt

---

### Option 7 — Production Deployment & DevOps 🚢
**Complexity:** Medium | **Value:** Deployment-ready project

- [ ] **Prometheus + Grafana in Docker Compose** — add scrape config and a pre-built NexusAI Grafana dashboard (you already have the `/metrics` endpoint, just need the stack)
- [ ] Kubernetes manifests — `Deployment`, `Service`, `ConfigMap`, `HPA` for the gateway
- [ ] Terraform / Pulumi infrastructure-as-code for cloud deployment (AWS ECS or GCP Cloud Run)
- [ ] Multi-region deployment guide
- [ ] Auto-scaling configuration based on request rate and cache hit ratio
- [ ] Backup and disaster recovery procedures for Redis data

---

## Feature Map

```
NexusAI Gateway
│
├── ✅ Core inference pipeline (POST /infer)
│   ├── ✅ API key auth + sliding-window rate limiter
│   ├── ✅ Volatility classifier (bypass cache for real-time queries)
│   ├── ✅ Semantic vector cache (cosine ≥ 0.92)
│   │   ├── ✅ Redis backend + in-memory fallback
│   │   ├── ✅ Adaptive TTL (factual 24h / technical 6h / general 1h)   [Option 3]
│   │   ├── ✅ LRU eviction at CACHE_MAX_ENTRIES                         [Option 3]
│   │   ├── ✅ Access count + last_accessed tracking                     [Option 3]
│   │   └── ✅ Startup + on-demand cache warming                         [Option 3]
│   ├── ✅ sentence-transformers all-MiniLM-L6-v2 embedder              [Option 1]
│   └── ✅ LLM providers: Mock / Hugging Face / OpenAI
│
├── ✅ Observability (Option 2)
│   ├── ✅ Prometheus metrics registry (counters, histograms, gauges)
│   ├── ✅ GET /api/v1/metrics scrape endpoint
│   └── ✅ Monitoring dashboard tab (latency, similarity, rate limiter)
│
├── ✅ Admin API
│   ├── ✅ GET  /cache/stats
│   ├── ✅ DELETE /cache/clear
│   ├── ✅ POST   /cache/warm                                            [Option 3]
│   ├── ✅ DELETE /cache/evict/{id}                                      [Option 3]
│   └── ✅ GET    /cache/inspect/{id}                                    [Option 3]
│
├── ✅ Test suite — 117 tests (Option 6)
├── ✅ CI pipeline — GitHub Actions (test / lint / boot-check)
│
├── ⬜ Enterprise auth, multi-tenancy, billing                           [Option 4]
├── ⬜ Response streaming (SSE), multi-model routing                    [Option 5]
└── ⬜ Prometheus+Grafana Docker stack, Kubernetes, Terraform            [Option 7]
```

---

## Quick Start

```bash
# Docker (recommended)
docker compose up --build
# → http://localhost:8000

# Local Python
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**API Key (dev):** `sk-nexus-dev-demo-key`

**Key endpoints:**
```
POST   /api/v1/infer              Execute inference
GET    /api/v1/health             Gateway health check
GET    /api/v1/cache/stats        Cache telemetry
POST   /api/v1/cache/warm         Trigger cache warm-up
DELETE /api/v1/cache/evict/{id}   Remove one entry
GET    /api/v1/cache/inspect/{id} Full entry detail
GET    /api/v1/metrics            Prometheus scrape
GET    /docs                      Interactive API docs (Swagger)
```
