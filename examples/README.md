# NexusAI API Examples

This folder contains example code showing how to use the NexusAI Gateway API in different languages.

---

## 📁 Files

### 1. `python_client.py`
Complete Python client with example usage.

**Run it:**
```bash
# Install requests library
pip install requests

# Run the example
python examples/python_client.py
```

**Features:**
- Object-oriented client class
- Health check, inference, cache stats
- Demonstrates cache HIT, MISS, and BYPASS
- Error handling

---

### 2. `javascript_client.html`
Interactive web page using JavaScript Fetch API.

**Run it:**
```bash
# Option 1: Open directly
open examples/javascript_client.html

# Option 2: Use Python HTTP server
python -m http.server 8080
# Then visit: http://localhost:8080/examples/javascript_client.html
```

**Features:**
- Click buttons to test each API call
- Pretty-printed JSON output
- Shows all response fields
- No dependencies needed

---

### 3. `curl_examples.sh`
Shell script with cURL commands for all endpoints.

**Run it:**
```bash
# Make it executable
chmod +x examples/curl_examples.sh

# Run all examples
bash examples/curl_examples.sh
```

**Requires:**
- `curl` (usually pre-installed)
- `jq` for pretty JSON (optional)

Install jq:
```bash
# Mac
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Windows (with Chocolatey)
choco install jq
```

---

## 🚀 Quick Start

### 1. Start the Server

```bash
docker compose up
```

Server will be available at `http://localhost:8000`

### 2. Try an Example

**Python:**
```bash
python examples/python_client.py
```

**JavaScript:**
```bash
open examples/javascript_client.html
```

**cURL:**
```bash
bash examples/curl_examples.sh
```

---

## 📚 API Endpoints Used

All examples demonstrate these key endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/infer` | POST | Execute inference |
| `/api/v1/cache/stats` | GET | Cache statistics |
| `/api/v1/cache/clear` | DELETE | Clear cache |
| `/api/v1/cache/warm` | POST | Pre-load cache |
| `/api/v1/metrics` | GET | Prometheus metrics |

---

## 🔑 Authentication

All examples use the default API key:
```
sk-nexus-dev-demo-key
```

Pass it in the `X-API-Key` header:
```bash
curl -H "X-API-Key: sk-nexus-dev-demo-key" ...
```

---

## 💡 Common Use Cases

### Use Case 1: FAQ Bot

```python
from python_client import NexusAIClient

client = NexusAIClient()

faqs = [
    "How do I reset my password?",
    "What are your business hours?",
    "Do you offer refunds?"
]

for question in faqs:
    result = client.infer(question)
    print(f"Q: {question}")
    print(f"A: {result['response']}")
    print(f"Cached: {result['cache_hit']}\n")
```

### Use Case 2: Document Q&A

```python
documents = load_documents()  # Your document loader

for doc in documents:
    # Extract key questions from doc
    questions = extract_questions(doc)
    
    for q in questions:
        answer = client.infer(q)
        save_answer(doc, q, answer['response'])
```

### Use Case 3: Batch Processing

```python
queries = read_queries_from_file('queries.txt')

for query in queries:
    result = client.infer(query)
    log_result(query, result)
```

---

## 🐛 Troubleshooting

### Error: Connection Refused

**Problem:** Server not running  
**Solution:** 
```bash
docker compose up
# Or check if it's running:
docker compose ps
```

### Error: 401 Unauthorized

**Problem:** Invalid API key  
**Solution:** Use the default key: `sk-nexus-dev-demo-key`

### Error: Module not found (Python)

**Problem:** Missing dependencies  
**Solution:**
```bash
pip install requests
```

---

## 📖 Learn More

- **Full API Docs:** http://localhost:8000/docs
- **Usage Guide:** ../USAGE_GUIDE.md
- **Main README:** ../README.md

---

## 🤝 Contributing

Have a useful example? PRs welcome!

Please add:
1. Working code
2. Comments explaining what it does
3. Instructions to run it
4. Required dependencies

---

**Happy coding! 🚀**
