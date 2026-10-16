#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# NexusAI — cURL Examples
# Collection of API requests using cURL for testing
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL="http://localhost:8000"
API_KEY="sk-nexus-dev-demo-key"

echo "🚀 NexusAI cURL Examples"
echo "========================"
echo ""

# ── Example 1: Health Check ────────────────────────────────────────────────────
echo "1. Health Check"
echo "   GET /api/v1/health"
curl -s $BASE_URL/api/v1/health | jq '.'
echo ""

# ── Example 2: First Query (Cache MISS) ────────────────────────────────────────
echo "2. First Query (Cache MISS expected)"
echo "   POST /api/v1/infer"
curl -s -X POST $BASE_URL/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "mock"
  }' | jq '.cache_hit, .latency_ms, .response[0:80]'
echo ""

# ── Example 3: Similar Query (Cache HIT) ───────────────────────────────────────
echo "3. Similar Query (Cache HIT expected)"
echo "   POST /api/v1/infer"
curl -s -X POST $BASE_URL/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What is France'\''s capital city?",
    "provider": "mock"
  }' | jq '.cache_hit, .similarity_score, .latency_ms'
echo ""

# ── Example 4: Volatile Query (Bypass) ─────────────────────────────────────────
echo "4. Volatile Query (Bypass expected)"
echo "   POST /api/v1/infer"
curl -s -X POST $BASE_URL/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What is the weather today in Tokyo?",
    "provider": "mock"
  }' | jq '.bypassed_due_to_volatility, .latency_ms'
echo ""

# ── Example 5: Bypass Cache (Force Fresh) ──────────────────────────────────────
echo "5. Force Bypass Cache"
echo "   POST /api/v1/infer (with bypass_cache: true)"
curl -s -X POST $BASE_URL/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "mock",
    "bypass_cache": true
  }' | jq '.cache_hit, .latency_ms'
echo ""

# ── Example 6: Cache Statistics ────────────────────────────────────────────────
echo "6. Cache Statistics"
echo "   GET /api/v1/cache/stats"
curl -s $BASE_URL/api/v1/cache/stats \
  -H "X-API-Key: $API_KEY" | jq '{
    total_entries,
    hits,
    misses,
    hit_ratio,
    storage_backend
  }'
echo ""

# ── Example 7: Warm Cache ──────────────────────────────────────────────────────
echo "7. Warm Cache (Pre-load Common Queries)"
echo "   POST /api/v1/cache/warm"
curl -s -X POST $BASE_URL/api/v1/cache/warm \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "provider": "mock",
    "model": "nexus-mock-v1"
  }' | jq '.'
echo ""

# ── Example 8: Clear Cache ─────────────────────────────────────────────────────
echo "8. Clear Cache"
echo "   DELETE /api/v1/cache/clear"
curl -s -X DELETE $BASE_URL/api/v1/cache/clear \
  -H "X-API-Key: $API_KEY" | jq '.'
echo ""

# ── Example 9: Prometheus Metrics ──────────────────────────────────────────────
echo "9. Prometheus Metrics (first 10 lines)"
echo "   GET /api/v1/metrics"
curl -s $BASE_URL/api/v1/metrics | head -n 10
echo "   ... (truncated)"
echo ""

# ── Example 10: Admin - List Keys ──────────────────────────────────────────────
echo "10. Admin - List API Keys"
echo "    GET /admin/keys"
curl -s $BASE_URL/api/v1/admin/keys \
  -H "X-API-Key: sk-nexus-admin-master-key" | jq '.[0:2]'
echo ""

echo "✅ All examples completed!"
echo ""
echo "💡 Tips:"
echo "   - Install jq for pretty JSON: apt-get install jq"
echo "   - Run with: bash examples/curl_examples.sh"
echo "   - Edit BASE_URL if not using localhost"
