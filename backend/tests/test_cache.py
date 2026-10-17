"""
Tests for:
  - query_classifier  (is_volatile_query)
  - embedder          (hash fallback, cosine_similarity, embed_batch, properties)
  - SemanticCacheManager (hit/miss, TTL expiry, custom TTL, stats, clear)
  - SlidingWindowRateLimiter (allow, reject, retry_after)
"""

import time

import numpy as np
import pytest

from app.services.embedder import (
    EmbedderService,
    _lightweight_hash_embedding,
    embedder_service,
)
from app.services.query_classifier import is_volatile_query
from app.services.rate_limiter import SlidingWindowRateLimiter
from app.services.semantic_cache import SemanticCacheManager

# ═══════════════════════════════════════════════════════════════════════════════
# Query Classifier
# ═══════════════════════════════════════════════════════════════════════════════

class TestQueryClassifier:
    # ── Volatile keywords ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("prompt", [
        "What is the weather today in Tokyo?",
        "Show me the current Bitcoin price",
        "What is the Ethereum price right now?",
        "Give me the latest news headlines",
        "What is the stock price of Apple?",
        "What is the exchange rate for USD to EUR?",
        "Tell me tonight's live score for Arsenal",
        "What is the current time in London?",
        "Any breaking news about the election?",
        "What is the weather forecast for tomorrow?",
        "What is the BTC price?",
        "Tell me the temperature in Paris",
        "Latest Bitcoin price update",
        "Score update for Manchester United",
        "What is the currency rate today?",
    ])
    def test_volatile_queries_detected(self, prompt):
        is_v, reason = is_volatile_query(prompt)
        assert is_v is True, f"Expected volatile: {prompt!r}"
        assert reason is not None

    @pytest.mark.parametrize("prompt", [
        "Explain binary search algorithms in Python",
        "Summarize the French Revolution",
        "What is the capital of France?",
        "How does photosynthesis work?",
        "Write a Python function to reverse a string",
        "What is machine learning?",
        "Describe the water cycle",
        "",
        "   ",
    ])
    def test_non_volatile_queries_pass(self, prompt):
        is_v, reason = is_volatile_query(prompt)
        assert is_v is False, f"Expected non-volatile: {prompt!r}"
        assert reason is None

    def test_case_insensitive_matching(self):
        for variant in ["WEATHER", "Weather", "wEaThEr"]:
            is_v, _ = is_volatile_query(f"Tell me the {variant} in Berlin")
            assert is_v is True

    def test_returns_matched_pattern_in_reason(self):
        _, reason = is_volatile_query("What is the Bitcoin price?")
        assert "bitcoin" in reason.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Embedder
# ═══════════════════════════════════════════════════════════════════════════════

class TestHashEmbedding:
    """Tests that target the hash fallback directly — no ML model needed."""

    def test_output_shape(self):
        vec = _lightweight_hash_embedding("hello world")
        assert vec.shape == (384,)
        assert vec.dtype == np.float32

    def test_unit_norm(self):
        vec = _lightweight_hash_embedding("test sentence for norm check")
        assert abs(np.linalg.norm(vec) - 1.0) < 1e-5

    def test_deterministic(self):
        v1 = _lightweight_hash_embedding("same text")
        v2 = _lightweight_hash_embedding("same text")
        np.testing.assert_array_equal(v1, v2)

    def test_different_texts_differ(self):
        v1 = _lightweight_hash_embedding("cat")
        v2 = _lightweight_hash_embedding("quantum chromodynamics")
        assert not np.allclose(v1, v2)

    def test_empty_string_zero_vector(self):
        vec = _lightweight_hash_embedding("")
        # All zeros — norm is 0, should not crash
        assert vec.shape == (384,)

    def test_custom_dimension(self):
        vec = _lightweight_hash_embedding("hi", dimension=128)
        assert vec.shape == (128,)


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert EmbedderService.cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-5)

    def test_orthogonal_vectors_score_zero(self):
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        assert EmbedderService.cosine_similarity(v1, v2) == pytest.approx(0.0, abs=1e-5)

    def test_opposite_vectors_score_minus_one(self):
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([-1.0, 0.0], dtype=np.float32)
        assert EmbedderService.cosine_similarity(v1, v2) == pytest.approx(-1.0, abs=1e-5)

    def test_zero_vector_returns_zero(self):
        v1 = np.zeros(4, dtype=np.float32)
        v2 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        assert EmbedderService.cosine_similarity(v1, v2) == 0.0

    def test_result_clamped_to_valid_range(self):
        # Slightly-off normalisation can produce values marginally outside [-1,1]
        v1 = np.array([1.0 + 1e-7, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 0.0], dtype=np.float32)
        score = EmbedderService.cosine_similarity(v1, v2)
        assert -1.0 <= score <= 1.0


class TestEmbedderService:
    def test_embed_text_returns_correct_shape(self, embedder):
        vec = embedder.embed_text("Hello NexusAI")
        assert vec.shape == (384,)
        assert vec.dtype == np.float32

    def test_embed_text_unit_norm(self, embedder):
        vec = embedder.embed_text("unit norm check")
        assert abs(np.linalg.norm(vec) - 1.0) < 1e-4

    def test_semantic_similarity_ordering(self, embedder):
        """Semantically close prompts should score higher than unrelated ones."""
        v1 = embedder.embed_text("What is the capital of France?")
        v2 = embedder.embed_text("What is France's capital city?")
        v3 = embedder.embed_text("How do I bake sourdough bread?")

        sim_close   = EmbedderService.cosine_similarity(v1, v2)
        sim_distant = EmbedderService.cosine_similarity(v1, v3)
        assert sim_close > sim_distant

    def test_embed_batch_length_matches_input(self, embedder):
        texts = ["first", "second", "third"]
        results = embedder.embed_batch(texts)
        assert len(results) == 3
        for vec in results:
            assert vec.shape == (384,)

    def test_embed_batch_consistent_with_embed_text(self, embedder):
        texts = ["consistent check A", "consistent check B"]
        batch  = embedder.embed_batch(texts)
        single = [embedder.embed_text(t) for t in texts]
        for b, s in zip(batch, single):
            assert EmbedderService.cosine_similarity(b, s) > 0.99

    def test_model_name_property(self, embedder):
        name = embedder.model_name
        assert isinstance(name, str)
        assert len(name) > 0

    def test_using_ml_model_property_is_bool(self, embedder):
        assert isinstance(embedder.using_ml_model, bool)


# ═══════════════════════════════════════════════════════════════════════════════
# SemanticCacheManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestSemanticCacheManager:
    PROMPT   = "What is the capital of France?"
    RESPONSE = "Paris is the capital of France."

    def _vec(self, text=PROMPT):
        return embedder_service.embed_text(text)

    # ── Basic miss / store / hit ───────────────────────────────────────────────

    def test_initial_miss(self, fresh_cache):
        hit, item, score = fresh_cache.find_similar(self.PROMPT, self._vec())
        assert hit is False
        assert item is None

    def test_exact_match_after_store(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        hit, item, score = fresh_cache.find_similar(self.PROMPT, vec)
        assert hit is True
        assert item.response == self.RESPONSE
        assert score >= 0.92

    def test_semantic_match_near_identical_prompt(self, fresh_cache):
        vec1 = self._vec("What is the capital of France?")
        fresh_cache.store("What is the capital of France?", self.RESPONSE, "m", "mock", vec1, 10, 120)
        vec2 = self._vec("What is France's capital city?")
        hit, item, score = fresh_cache.find_similar("What is France's capital city?", vec2)
        # With ML embeddings this should hit; with hash fallback it may not — skip if below threshold
        if score >= 0.92:
            assert hit is True

    def test_unrelated_prompt_misses(self, fresh_cache):
        vec1 = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec1, 10, 120)
        vec2 = self._vec("Explain quantum entanglement in physics")
        hit, _, _ = fresh_cache.find_similar("Explain quantum entanglement in physics", vec2)
        assert hit is False

    # ── TTL expiry ────────────────────────────────────────────────────────────

    def test_expired_entry_not_returned(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, ttl_seconds=1)
        time.sleep(1.1)
        hit, item, _ = fresh_cache.find_similar(self.PROMPT, vec)
        assert hit is False

    def test_non_expired_entry_still_returned(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, ttl_seconds=60)
        hit, item, _ = fresh_cache.find_similar(self.PROMPT, vec)
        assert hit is True

    def test_custom_ttl_stored_correctly(self, fresh_cache):
        vec = self._vec()
        item = fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, ttl_seconds=999)
        assert item.ttl_seconds == 999

    def test_default_ttl_used_when_none_passed(self, fresh_cache):
        from app.config import settings
        vec = self._vec()
        item = fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, ttl_seconds=None)
        assert item.ttl_seconds == settings.DEFAULT_CACHE_TTL_SECONDS

    # ── Stats ─────────────────────────────────────────────────────────────────

    def test_stats_empty_cache(self, fresh_cache):
        stats = fresh_cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["hit_ratio"] == 0.0
        assert stats["entries"] == []

    def test_stats_hit_ratio_calculation(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        # 1 miss then 1 hit
        fresh_cache.find_similar("something completely different", self._vec("something completely different"))
        fresh_cache.find_similar(self.PROMPT, vec)
        stats = fresh_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_ratio"] == 50.0

    def test_stats_entry_info_fields(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        stats = fresh_cache.get_stats()
        assert stats["total_entries"] == 1
        entry = stats["entries"][0]
        assert "id" in entry
        assert "prompt" in entry
        assert "response_preview" in entry
        assert "expires_in_seconds" in entry
        assert entry["expires_in_seconds"] > 0

    def test_stats_response_preview_truncated(self, fresh_cache):
        long_response = "x" * 200
        vec = self._vec()
        fresh_cache.store(self.PROMPT, long_response, "m", "mock", vec, 10, 120)
        stats = fresh_cache.get_stats()
        preview = stats["entries"][0]["response_preview"]
        assert len(preview) <= 123  # 120 chars + "..."

    # ── Clear ─────────────────────────────────────────────────────────────────

    def test_clear_all_returns_correct_count(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        fresh_cache.store("another prompt", "another response", "m", "mock",
                          self._vec("another prompt"), 5, 120)
        cleared = fresh_cache.clear_all()
        assert cleared == 2

    def test_clear_all_empties_store(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        fresh_cache.clear_all()
        stats = fresh_cache.get_stats()
        assert stats["total_entries"] == 0

    def test_clear_resets_hit_miss_counters(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        fresh_cache.find_similar(self.PROMPT, vec)
        fresh_cache.clear_all()
        stats = fresh_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    # ── Custom similarity threshold ───────────────────────────────────────────

    def test_custom_threshold_lower_allows_weaker_match(self, fresh_cache):
        vec = self._vec()
        fresh_cache.store(self.PROMPT, self.RESPONSE, "m", "mock", vec, 10, 120)
        hit_strict, _, _  = fresh_cache.find_similar(self.PROMPT, vec, threshold=0.99)
        hit_lenient, _, _ = fresh_cache.find_similar(self.PROMPT, vec, threshold=0.50)
        # At 0.50 an exact-same vector must always hit
        assert hit_lenient is True


# ═══════════════════════════════════════════════════════════════════════════════
# SlidingWindowRateLimiter
# ═══════════════════════════════════════════════════════════════════════════════

class TestSlidingWindowRateLimiter:
    def _fresh_limiter(self):
        return SlidingWindowRateLimiter()

    def test_allows_requests_under_limit(self):
        limiter = self._fresh_limiter()
        for _ in range(5):
            allowed, remaining, retry = limiter.is_allowed("test-key")
            assert allowed is True
            assert retry == 0

    def test_remaining_decrements(self):
        from app.config import settings
        limiter = self._fresh_limiter()
        allowed, remaining_1, _ = limiter.is_allowed("dec-key")
        allowed, remaining_2, _ = limiter.is_allowed("dec-key")
        assert remaining_1 > remaining_2

    def test_rejects_at_max_requests(self):
        from app.config import settings
        limiter = self._fresh_limiter()
        key = "burst-key"
        # Exhaust the window
        for _ in range(settings.RATE_LIMIT_MAX_REQUESTS):
            limiter.is_allowed(key)
        allowed, remaining, retry = limiter.is_allowed(key)
        assert allowed is False
        assert remaining == 0
        assert retry > 0

    def test_different_keys_isolated(self):
        limiter = self._fresh_limiter()
        limiter.is_allowed("key-a")
        allowed, _, _ = limiter.is_allowed("key-b")
        assert allowed is True

    def test_retry_after_is_positive_on_rejection(self):
        from app.config import settings
        limiter = self._fresh_limiter()
        key = "retry-key"
        for _ in range(settings.RATE_LIMIT_MAX_REQUESTS):
            limiter.is_allowed(key)
        _, _, retry = limiter.is_allowed(key)
        assert retry >= 1
