import pytest
import numpy as np
from app.services.query_classifier import is_volatile_query
from app.services.embedder import embedder_service
from app.services.semantic_cache import SemanticCacheManager
from app.services.rate_limiter import SlidingWindowRateLimiter


def test_query_classifier():
    # Volatile queries should be detected
    is_v, reason = is_volatile_query("What is the weather today in Tokyo?")
    assert is_v is True
    assert reason is not None

    is_v, _ = is_volatile_query("Show me the latest Bitcoin price right now")
    assert is_v is True

    # Deterministic queries should NOT be marked volatile
    is_v, _ = is_volatile_query("Explain binary search algorithms in Python")
    assert is_v is False

    is_v, _ = is_volatile_query("Summarize this article about quantum mechanics")
    assert is_v is False


def test_embedder_similarity():
    v1 = embedder_service.embed_text("What is the capital of France?")
    v2 = embedder_service.embed_text("What is France's capital city?")
    v3 = embedder_service.embed_text("How do I bake sourdough bread?")

    sim_related = embedder_service.cosine_similarity(v1, v2)
    sim_unrelated = embedder_service.cosine_similarity(v1, v3)

    assert sim_related > sim_unrelated
    assert sim_related > 0.50
    assert sim_unrelated < 0.35


def test_semantic_cache_hit_and_miss():
    cache = SemanticCacheManager()
    cache.clear_all()

    prompt1 = "What is the capital of France?"
    vec1 = embedder_service.embed_text(prompt1)
    
    # Initially should be a MISS
    hit, item, score = cache.find_similar(prompt1, vec1)
    assert hit is False

    # Store response
    cache.store(
        prompt=prompt1,
        response="Paris is the capital of France.",
        model="mock-v1",
        provider="mock",
        vector=vec1,
        tokens=15,
        ttl_seconds=60
    )

    # Exact or near identical prompt should HIT
    hit, item, score = cache.find_similar(prompt1, vec1)
    assert hit is True
    assert item is not None
    assert item.response == "Paris is the capital of France."
    assert score >= 0.92

    # Completely different prompt should MISS
    prompt_diff = "Explain quantum entanglement in physics"
    vec_diff = embedder_service.embed_text(prompt_diff)
    hit_diff, _, _ = cache.find_similar(prompt_diff, vec_diff)
    assert hit_diff is False


def test_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    client_id = "test-rate-key"

    # Make multiple requests
    for i in range(10):
        allowed, remaining, _ = limiter.is_allowed(client_id)
        assert allowed is True
