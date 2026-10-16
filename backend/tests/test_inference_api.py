"""
FastAPI integration tests using TestClient.

Covers:
  GET  /api/v1/health
  POST /api/v1/infer   — miss, hit, volatile bypass, bypass_cache flag,
                          missing key (401), wrong key (403), custom TTL,
                          response headers (X-Cache, X-Response-Time-Ms)
  GET  /api/v1/cache/stats
  DELETE /api/v1/cache/clear
  GET  /api/v1/metrics

Every test that touches the cache or rate-limiter is decorated with the
`isolated_api_cache` and `allow_all_rate_limiter` fixtures from conftest.py
so tests are fully independent of each other and of run order.
"""

import pytest

VALID_KEY = "sk-nexus-dev-demo-key"
INVALID_KEY = "sk-totally-wrong"
INFER_URL = "/api/v1/infer"
HEALTH_URL = "/api/v1/health"
STATS_URL = "/api/v1/cache/stats"
CLEAR_URL = "/api/v1/cache/clear"
METRICS_URL = "/api/v1/metrics"


# ── helpers ───────────────────────────────────────────────────────────────────

def _infer(client, prompt, *, key=VALID_KEY, bypass_cache=False, provider="mock"):
    return client.post(
        INFER_URL,
        json={"prompt": prompt, "provider": provider, "bypass_cache": bypass_cache},
        headers={"X-API-Key": key},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Health endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    def test_returns_200(self, client):
        r = client.get(HEALTH_URL)
        assert r.status_code == 200

    def test_response_schema(self, client):
        data = client.get(HEALTH_URL).json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "backend_storage" in data
        assert "default_provider" in data
        assert "embedder_ready" in data

    def test_embedder_ready_is_bool(self, client):
        data = client.get(HEALTH_URL).json()
        assert isinstance(data["embedder_ready"], bool)

    def test_no_auth_required(self, client):
        # Health must be reachable without an API key
        r = client.get(HEALTH_URL)
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# Authentication & rate-limiting guard (deps.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    def test_missing_key_returns_401(self, client, isolated_api_cache):
        r = client.post(INFER_URL, json={"prompt": "test"})
        assert r.status_code == 401
        assert "Missing API Key" in r.json()["detail"]

    def test_wrong_key_returns_403(self, client, isolated_api_cache):
        r = client.post(
            INFER_URL,
            json={"prompt": "test"},
            headers={"X-API-Key": INVALID_KEY},
        )
        assert r.status_code == 403
        assert "Invalid API Key" in r.json()["detail"]

    def test_valid_key_via_header(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is the capital of France?")
        assert r.status_code == 200

    def test_valid_key_via_query_param(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = client.post(
            INFER_URL + f"?api_key={VALID_KEY}",
            json={"prompt": "What is the capital of France?"},
        )
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# /infer endpoint — core behaviour
# ═══════════════════════════════════════════════════════════════════════════════

class TestInferEndpoint:
    def test_cache_miss_on_first_request(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is the capital of France?")
        assert r.status_code == 200
        data = r.json()
        assert data["cache_hit"] is False
        assert data["bypassed_due_to_volatility"] is False
        assert data["response"] != ""
        assert data["latency_ms"] >= 0

    def test_cache_hit_on_second_identical_request(self, client, isolated_api_cache, allow_all_rate_limiter):
        prompt = "What is the capital of France?"
        _infer(client, prompt)          # seed the cache
        r2 = _infer(client, prompt)     # should be a HIT
        assert r2.status_code == 200
        data = r2.json()
        assert data["cache_hit"] is True
        assert data["similarity_score"] is not None
        assert data["similarity_score"] >= 0.92

    def test_volatile_query_bypasses_cache(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is the weather today in Tokyo?")
        assert r.status_code == 200
        data = r.json()
        assert data["bypassed_due_to_volatility"] is True
        assert data["cache_hit"] is False

    def test_bypass_cache_flag_forces_miss(self, client, isolated_api_cache, allow_all_rate_limiter):
        prompt = "Explain binary search"
        _infer(client, prompt)  # prime cache
        r = _infer(client, prompt, bypass_cache=True)
        assert r.status_code == 200
        data = r.json()
        assert data["cache_hit"] is False

    def test_response_contains_required_fields(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is machine learning?")
        data = r.json()
        required = {"prompt", "response", "model", "provider", "cache_hit",
                    "latency_ms", "tokens_used", "bypassed_due_to_volatility", "timestamp"}
        assert required.issubset(data.keys())

    def test_response_prompt_echoes_input(self, client, isolated_api_cache, allow_all_rate_limiter):
        prompt = "Explain recursion in programming"
        r = _infer(client, prompt)
        assert r.json()["prompt"] == prompt

    def test_provider_field_reflects_mock(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "Hello world", provider="mock")
        assert r.json()["provider"] == "mock"

    def test_tokens_used_is_positive(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is the capital of France?")
        assert r.json()["tokens_used"] > 0

    def test_x_cache_header_miss(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "unique prompt xyz 12345")
        assert r.headers.get("x-cache") == "MISS"

    def test_x_cache_header_hit(self, client, isolated_api_cache, allow_all_rate_limiter):
        prompt = "header hit test prompt"
        _infer(client, prompt)
        r2 = _infer(client, prompt)
        assert r2.headers.get("x-cache") == "HIT"

    def test_x_response_time_header_present(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "timing check prompt")
        assert "x-response-time-ms" in r.headers

    def test_x_cache_similarity_present_on_hit(self, client, isolated_api_cache, allow_all_rate_limiter):
        prompt = "similarity header test"
        _infer(client, prompt)
        r2 = _infer(client, prompt)
        assert "x-cache-similarity" in r2.headers

    def test_mock_capital_france_response(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "What is the capital of France?")
        assert "Paris" in r.json()["response"]

    def test_mock_summary_branch(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "Please summarize this text for me")
        assert "Summary" in r.json()["response"]

    def test_mock_translate_branch(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "Translate this sentence to French")
        assert "Translation" in r.json()["response"] or r.json()["response"] != ""

    def test_mock_code_branch(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = _infer(client, "Write Python code to sort a list")
        assert r.status_code == 200

    def test_empty_prompt_returns_422(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = client.post(
            INFER_URL,
            json={"prompt": ""},
            headers={"X-API-Key": VALID_KEY},
        )
        assert r.status_code == 422

    def test_custom_ttl_accepted(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = client.post(
            INFER_URL,
            json={"prompt": "custom ttl test prompt", "provider": "mock", "custom_ttl_seconds": 30},
            headers={"X-API-Key": VALID_KEY},
        )
        assert r.status_code == 200
        assert r.json()["cache_hit"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Cache admin endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestCacheAdminEndpoints:
    def test_stats_returns_200(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = client.get(STATS_URL, headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_stats_schema(self, client, isolated_api_cache, allow_all_rate_limiter):
        data = client.get(STATS_URL, headers={"X-API-Key": VALID_KEY}).json()
        required = {"total_entries", "hits", "misses", "hit_ratio", "storage_backend", "entries"}
        assert required.issubset(data.keys())

    def test_stats_empty_initially(self, client, isolated_api_cache, allow_all_rate_limiter):
        data = client.get(STATS_URL, headers={"X-API-Key": VALID_KEY}).json()
        assert data["total_entries"] == 0
        assert data["entries"] == []

    def test_stats_reflects_cached_entry(self, client, isolated_api_cache, allow_all_rate_limiter):
        _infer(client, "Stats reflection test prompt")
        data = client.get(STATS_URL, headers={"X-API-Key": VALID_KEY}).json()
        assert data["total_entries"] == 1

    def test_clear_returns_200(self, client, isolated_api_cache, allow_all_rate_limiter):
        r = client.delete(CLEAR_URL, headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_clear_response_schema(self, client, isolated_api_cache, allow_all_rate_limiter):
        data = client.delete(CLEAR_URL, headers={"X-API-Key": VALID_KEY}).json()
        assert "cleared_entries" in data
        assert "status" in data
        assert data["status"] == "success"

    def test_clear_empties_cache(self, client, isolated_api_cache, allow_all_rate_limiter):
        _infer(client, "To be cleared test prompt")
        client.delete(CLEAR_URL, headers={"X-API-Key": VALID_KEY})
        data = client.get(STATS_URL, headers={"X-API-Key": VALID_KEY}).json()
        assert data["total_entries"] == 0

    def test_clear_returns_count_of_deleted_entries(self, client, isolated_api_cache, allow_all_rate_limiter):
        _infer(client, "Entry one for clear count test")
        _infer(client, "Entry two for clear count test")
        data = client.delete(CLEAR_URL, headers={"X-API-Key": VALID_KEY}).json()
        assert data["cleared_entries"] >= 1

    def test_stats_requires_auth(self, client, isolated_api_cache):
        r = client.get(STATS_URL)
        assert r.status_code == 401

    def test_clear_requires_auth(self, client, isolated_api_cache):
        r = client.delete(CLEAR_URL)
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus metrics endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoint:
    def test_returns_200(self, client):
        r = client.get(METRICS_URL)
        assert r.status_code == 200

    def test_content_type_is_prometheus(self, client):
        r = client.get(METRICS_URL)
        assert "text/plain" in r.headers["content-type"]

    def test_body_contains_nexusai_prefix(self, client):
        body = client.get(METRICS_URL).text
        assert "nexusai_" in body

    def test_known_metric_names_present(self, client):
        body = client.get(METRICS_URL).text
        for name in [
            "nexusai_inference_requests_total",
            "nexusai_cache_hits_total",
            "nexusai_cache_misses_total",
            "nexusai_embed_requests_total",
            "nexusai_rate_limit_allowed_total",
            "nexusai_volatile_queries_total",
        ]:
            assert name in body, f"Metric {name!r} not found in /metrics output"

    def test_no_auth_required(self, client):
        # Metrics endpoint must be scrapable without credentials
        r = client.get(METRICS_URL)
        assert r.status_code == 200
