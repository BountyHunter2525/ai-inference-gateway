# NexusAI — Complete Usage Guide

Step-by-step guide to using NexusAI with screenshots and examples.

---

## 📖 Table of Contents

1. [Installation](#installation)
2. [Starting the Application](#starting-the-application)
3. [Using the Web Playground](#using-the-web-playground)
4. [API Usage Examples](#api-usage-examples)
5. [Admin Panel Guide](#admin-panel-guide)
6. [Monitoring Dashboard](#monitoring-dashboard)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### Option 1: Docker (Recommended)

**Requirements:**
- Docker Desktop installed
- 4GB free RAM
- Internet connection

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway

# 2. Start everything with one command
docker compose up

# 3. Wait for "Application startup complete" message

# 4. Open browser to http://localhost:8000
```

**Expected Output:**
```
✔ Container nexusai-redis-1    Created
✔ Container nexusai-gateway-1  Created
Attaching to nexusai-gateway-1, nexusai-redis-1
nexusai-redis-1    | Ready to accept connections
nexusai-gateway-1  | INFO: Application startup complete.
nexusai-gateway-1  | INFO: Uvicorn running on http://0.0.0.0:8000
```

### Option 2: Local Python

**Requirements:**
- Python 3.11 or 3.12
- pip package manager

**Steps:**

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start server
python -m uvicorn app.main:app --reload

# 6. Open browser to http://localhost:8000
```

---

## 🚀 Starting the Application

### First-Time Setup

1. **Verify Installation**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "backend_storage": "REDIS",
     "embedder_ready": true
   }
   ```

2. **Access the Web Interface**
   - Open browser to `http://localhost:8000`
   - You should see the NexusAI playground

3. **Default API Key**
   - Use: `sk-nexus-dev-demo-key`
   - This is pre-configured and ready to use

---

## 🎨 Using the Web Playground

### Tab 1: Playground (Testing Inference)

**Screenshot Location: [Your playground with all tabs visible]**

#### Step 1: Enter Your API Key
- Find the "Gateway API Key" input field at the top
- Default key is already filled: `sk-nexus-dev-demo-key`
- Keep it as-is for testing

#### Step 2: Choose Provider
- **Mock Engine** - Instant responses, perfect for testing
- **Hugging Face API** - Free, requires API token
- **OpenAI** - Paid, requires API key

**For testing, use Mock Engine!**

#### Step 3: Try Your First Query

1. Click the sample button: **"Capital of France"**
2. Click **"Execute Inference"** button
3. Watch the result appear below

**First Result (Cache MISS):**
```
Badge: CACHE MISS · FACTUAL TTL
Latency: ~12ms
Tokens: 42
Response: "The capital of France is Paris..."
```

4. Now click: **"France's capital (Semantic Match)"**
5. Click **"Execute Inference"** again

**Second Result (Cache HIT):**
```
Badge: CACHE HIT
Latency: ~5ms (400% faster!)
Similarity: 94%
Response: [Same cached response]
```

#### Step 4: Try a Live Query

1. Click: **"Weather today (Volatile)"**
2. Click **"Execute Inference"**

**Result (Bypassed Cache):**
```
Badge: REALTIME BYPASS
Latency: ~10ms
Response: "I cannot provide real-time weather..."
```

Notice how it automatically bypassed the cache!

### Understanding the Response Panel

**Color-Coded Badges:**
- 🟢 **CACHE HIT** - Query was found in cache (super fast)
- 🔵 **CACHE MISS** - First time query (stored for next time)
- 🟡 **REALTIME BYPASS** - Live data query (intentionally not cached)

**Metrics:**
- **Latency** - How long the request took
- **Tokens** - How many tokens used (for cost calculation)
- **Similarity** - Only shown on cache hits (how similar to cached query)

### Cache Telemetry Panel

**Right side of Playground tab shows:**

1. **Cache Statistics**
   - Hit Ratio: % of requests served from cache
   - Cached Queries: Total entries stored
   - Storage Backend: REDIS or MEMORY

2. **Active Cached Entries**
   - Each entry shows:
     - The original prompt
     - TTL remaining (time until expiry)
     - Category (factual/technical/general)
     - Hit count
     - Entry ID

3. **Flush Cache Button**
   - Clears all cached entries
   - Use when testing

---

## 📊 API Usage Examples

### Example 1: Basic Inference

```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "mock"
  }'
```

**Response:**
```json
{
  "prompt": "What is the capital of France?",
  "response": "The capital of France is Paris.",
  "model": "nexus-mock-v1",
  "provider": "mock",
  "cache_hit": false,
  "similarity_score": null,
  "latency_ms": 12.4,
  "tokens_used": 42,
  "bypassed_due_to_volatility": false,
  "ttl_category": "factual",
  "timestamp": 1729094123.45
}
```

### Example 2: Bypass Cache

```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "mock",
    "bypass_cache": true
  }'
```

### Example 3: Using HuggingFace (Real AI)

```bash
# Set your HuggingFace token first
export HUGGINGFACE_API_TOKEN=hf_your_token_here

curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "provider": "huggingface",
    "model": "google/flan-t5-base"
  }'
```

### Example 4: Check Cache Stats

```bash
curl http://localhost:8000/api/v1/cache/stats \
  -H "X-API-Key: sk-nexus-dev-demo-key"
```

**Response:**
```json
{
  "total_entries": 5,
  "hits": 12,
  "misses": 5,
  "hit_ratio": 70.6,
  "storage_backend": "REDIS",
  "max_entries": 500,
  "entries": [...]
}
```

### Example 5: Clear Cache

```bash
curl -X DELETE http://localhost:8000/api/v1/cache/clear \
  -H "X-API-Key: sk-nexus-dev-demo-key"
```

---

## 🔑 Admin Panel Guide

### Accessing Admin Panel

1. Click **"Admin"** tab in the web interface
2. You'll need an admin API key

**Default Admin Key:** `sk-nexus-admin-master-key`

### Dashboard Overview

**Top Section Shows:**
- Total active API keys
- Number of unique tenants
- Audit events logged today

### Creating a New API Key

**Step-by-step:**

1. **Fill in the form:**
   - **Key Name**: `My Test Key` (required)
   - **Role**: Select `user` or `admin`
   - **Tenant ID**: `test-tenant` (optional, for multi-tenancy)
   - **Request Quota**: `1000` (daily limit)
   - **Token Quota**: `100000` (daily token limit)
   - **Description**: `Testing key for demo` (optional)

2. **Click "Create API Key"**

3. **Save the Key!** 
   - The key is shown ONCE
   - Copy it immediately: `sk_xxxxxxxxxxxxxxxx`
   - Click the "Copy" button

4. **Key appears in the list below**

### Managing Existing Keys

**Each key card shows:**
- Key preview (first 16 characters)
- Role and tenant
- Status (Active/Revoked)
- Quota bars showing usage:
  - Blue bar: Request usage
  - Purple bar: Token usage
  - Percentage filled

**Actions:**
- **📊 Usage** - View detailed quota breakdown
- **🔒 Revoke** - Disable the key (cannot be undone)

### Audit Log

**View all API activity:**
- Who called what endpoint
- When it happened
- Success or failure
- Event types:
  - 🟢 `key_created` - New key created
  - 🔴 `key_revoked` - Key disabled
  - 🟡 `quota_exceeded` - Quota limit hit
  - 🔵 `inference` - Normal API call

**Filtering:**
- Filter by tenant ID
- Filter by event type
- Click "Apply Filters"

**Clearing:**
- Click "Clear Audit Log" to remove all entries
- Requires confirmation

---

## 📈 Monitoring Dashboard

### Tab 2: Monitoring

**Auto-refreshes every 6 seconds**

### Key Metrics

**Row 1: System Health**
- **Embedding Backend** - Which ML model is active
- **Total Encodes** - How many embeddings generated
- **Embed Latency p50** - Median embedding time

**Row 2: Throughput**
- **Cache Hits** - Successful cache retrievals
- **Cache Misses** - New queries cached
- **Volatile Bypasses** - Real-time queries
- **Tokens Used** - Total tokens processed

**Row 3: Latency Percentiles**
Shows p50, p90, p99 latency for:
- Cache hit requests (~5ms)
- Cache miss requests (~500ms)
- Embedding generation (~50ms)

**Row 4: Advanced Cache**
- **Evictions** - Entries removed (LRU)
- **Warm-up Entries** - Pre-loaded queries
- **Cache Capacity** - % of max entries used
- **Warm Cache Button** - Pre-load common queries

**Row 5: Cache Analytics**
- **TTL Category Breakdown** - Factual/Technical/General
- **Top Accessed Entries** - Most popular queries

**Row 6: Similarity & Rate Limit**
- **Similarity Score Distribution** - Histogram
- **Rate Limiter** - Allowed vs rejected requests

**Bottom: Raw Prometheus Metrics**
- Actual metrics endpoint output
- Filter by metric name
- Useful for custom monitoring

---

## 💡 Common Use Cases

### Use Case 1: Building a Chatbot

```python
import requests

API_URL = "http://localhost:8000/api/v1/infer"
API_KEY = "sk-nexus-dev-demo-key"

def ask_question(question):
    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "prompt": question,
            "provider": "mock"
        }
    )
    return response.json()

# Test it
result = ask_question("What is Python?")
print(f"Answer: {result['response']}")
print(f"Cache Hit: {result['cache_hit']}")
print(f"Latency: {result['latency_ms']}ms")
```

### Use Case 2: FAQ System

```javascript
// JavaScript example for web apps
async function getFAQAnswer(question) {
  const response = await fetch('http://localhost:8000/api/v1/infer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'sk-nexus-dev-demo-key'
    },
    body: JSON.stringify({
      prompt: question,
      provider: 'mock'
    })
  });
  
  const data = await response.json();
  return {
    answer: data.response,
    fromCache: data.cache_hit,
    speed: data.latency_ms
  };
}

// Use it
const result = await getFAQAnswer("How do I reset my password?");
console.log(result);
```

### Use Case 3: Document Q&A

```python
# Batch processing with caching
documents = [
    "What is machine learning?",
    "Explain neural networks",
    "What is deep learning?",
    "How do neural networks work?"  # Similar to #2, will cache hit
]

for doc in documents:
    result = ask_question(doc)
    status = "⚡ CACHED" if result['cache_hit'] else "🔄 NEW"
    print(f"{status} | {result['latency_ms']}ms | {doc}")
```

---

## 🐛 Troubleshooting

### Problem: "Connection refused" error

**Solution:**
```bash
# Check if services are running
docker compose ps

# Restart if needed
docker compose restart
```

### Problem: Cache not working (always MISS)

**Possible causes:**
1. Redis not connected (check health endpoint)
2. Similarity threshold too high
3. Queries are too different

**Check:**
```bash
curl http://localhost:8000/api/v1/health
# Look for "backend_storage": "REDIS"
```

### Problem: Slow responses

**Solutions:**
1. Check if ML model is loaded:
   ```bash
   # Look for "embedder_ready": true
   curl http://localhost:8000/api/v1/health
   ```

2. First query after restart is slow (model loading)
3. Wait 30 seconds and try again

### Problem: API key not working

**Check:**
1. Using correct header: `X-API-Key` (not `X-Api-Key`)
2. No extra spaces in key
3. Key exists in config

**Test:**
```bash
# Should return 401 if key is wrong
curl -X POST http://localhost:8000/api/v1/infer \
  -H "X-API-Key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

### Problem: Out of memory

**Solutions:**
1. Reduce cache size in config:
   ```bash
   # In .env file
   CACHE_MAX_ENTRIES=100
   ```

2. Restart services:
   ```bash
   docker compose restart
   ```

---

## 📚 Next Steps

**After mastering the basics:**

1. **Read the API docs**: http://localhost:8000/docs
2. **Check metrics**: http://localhost:8000/api/v1/metrics
3. **Try different providers**: HuggingFace, OpenAI
4. **Experiment with parameters**: temperature, max_tokens
5. **Monitor performance**: Use the Monitoring tab
6. **Manage keys**: Create your own API keys

---

## 💬 Support

**Having issues?**

1. Check this guide first
2. Look at logs: `docker compose logs -f`
3. Read error messages carefully
4. Check GitHub issues
5. Google the error message

**Common resources:**
- FastAPI docs: https://fastapi.tiangolo.com
- Redis docs: https://redis.io/docs
- sentence-transformers: https://www.sbert.net

---

## 🎉 You're Ready!

You now know how to:
- ✅ Install and run NexusAI
- ✅ Use the web playground
- ✅ Make API requests
- ✅ Manage API keys
- ✅ Monitor performance
- ✅ Troubleshoot issues

**Happy caching! 🚀**
