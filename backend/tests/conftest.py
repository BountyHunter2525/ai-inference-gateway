"""
Shared pytest fixtures for NexusAI test suite.

Key design decisions:
- Every test that touches the semantic cache gets a *fresh* SemanticCacheManager
  instance (in-memory, no Redis) so tests are isolated and order-independent.
- The FastAPI TestClient is built once per session and reuses the real app,
  but the cache singleton is patched to a fresh instance before each API test.
- The rate-limiter is patched to always allow requests in API tests so tests
  don't accidentally trip the 30-req/min limit.
- Prometheus metrics use the global REGISTRY; counter values are cumulative
  across the process, so metric tests read the *delta* rather than absolute values.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.embedder import EmbedderService, _lightweight_hash_embedding
from app.services.semantic_cache import SemanticCacheManager

# ── Embedder ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def embedder():
    """
    Shared EmbedderService for the whole test session.
    Uses whatever backend is available (ML model or hash fallback).
    """
    return EmbedderService()


# ── Isolated in-memory cache ──────────────────────────────────────────────────

@pytest.fixture()
def fresh_cache():
    """
    A brand-new SemanticCacheManager with in-memory backend.
    Cleared before being handed to the test so nothing leaks between runs.
    """
    cache = SemanticCacheManager()
    cache.clear_all()
    return cache


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient wired to the real application.
    Scoped to the session so the app only starts once.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=False)
def isolated_api_cache(monkeypatch):
    """
    Replaces the module-level `semantic_cache` singleton used by the API
    with a fresh in-memory instance, then restores it after the test.
    Apply with:  @pytest.mark.usefixtures("isolated_api_cache")
    or by requesting this fixture explicitly.
    """
    import app.api.v1.cache_admin as admin_mod
    import app.api.v1.inference as inf_mod
    import app.services.rate_limiter as rl_mod

    fresh = SemanticCacheManager()
    fresh.clear_all()

    monkeypatch.setattr(inf_mod, "semantic_cache", fresh)
    monkeypatch.setattr(admin_mod, "semantic_cache", fresh)
    # Rate-limiter reads redis_client from the cache singleton — patch it too
    monkeypatch.setattr(rl_mod, "semantic_cache", fresh)
    return fresh


@pytest.fixture(autouse=False)
def allow_all_rate_limiter(monkeypatch):
    """
    Patches the rate limiter to always allow every request.
    Apply to API tests that aren't specifically testing rate-limiting behaviour.
    """
    import app.api.deps as deps_mod
    from app.services.rate_limiter import SlidingWindowRateLimiter

    unlimited = SlidingWindowRateLimiter()
    unlimited._memory_windows = {}  # ensure clean slate

    # Monkey-patch is_allowed to always return (True, 999, 0)
    monkeypatch.setattr(unlimited, "is_allowed", lambda key: (True, 999, 0))
    monkeypatch.setattr(deps_mod, "rate_limiter", unlimited)
    return unlimited
