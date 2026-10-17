"""
SemanticCacheManager
=====================
Redis-backed (with in-memory fallback) vector similarity cache.

Option-3 additions:
  - access_count + last_accessed fields on every CachedItem
  - LRU eviction when CACHE_MAX_ENTRIES is exceeded (oldest last_accessed goes first)
  - warm_from_list()  — bulk-store pre-computed (prompt, response) pairs
  - evict_entry()     — delete a single entry by id
  - get_entry()       — retrieve a full entry for the inspect endpoint
  - get_stats() returns top_entries sorted by access_count
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

import numpy as np
import redis

from app.config import settings
from app.services.embedder import embedder_service

logger = logging.getLogger(__name__)


def _metrics():
    from app.services import metrics as m  # noqa: PLC0415
    return m


# ─────────────────────────────────────────────────────────────────────────────
# CachedItem
# ─────────────────────────────────────────────────────────────────────────────

class CachedItem:
    def __init__(
        self,
        entry_id: str,
        prompt: str,
        response: str,
        model: str,
        provider: str,
        vector: np.ndarray,
        tokens: int,
        created_at: float,
        ttl_seconds: int,
        ttl_category: str = "general",
        access_count: int = 0,
        last_accessed: float | None = None,
    ):
        self.entry_id = entry_id
        self.prompt = prompt
        self.response = response
        self.model = model
        self.provider = provider
        self.vector = vector
        self.tokens = tokens
        self.created_at = created_at
        self.ttl_seconds = ttl_seconds
        self.ttl_category = ttl_category
        self.access_count = access_count
        self.last_accessed: float = last_accessed or created_at

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    def touch(self) -> None:
        """Increment access counter and update last-accessed timestamp."""
        self.access_count += 1
        self.last_accessed = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id":     self.entry_id,
            "prompt":       self.prompt,
            "response":     self.response,
            "model":        self.model,
            "provider":     self.provider,
            "vector":       self.vector.tolist(),
            "tokens":       self.tokens,
            "created_at":   self.created_at,
            "ttl_seconds":  self.ttl_seconds,
            "ttl_category": self.ttl_category,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CachedItem:
        return cls(
            entry_id=data["entry_id"],
            prompt=data["prompt"],
            response=data["response"],
            model=data["model"],
            provider=data["provider"],
            vector=np.array(data["vector"], dtype=np.float32),
            tokens=data.get("tokens", 0),
            created_at=data["created_at"],
            ttl_seconds=data["ttl_seconds"],
            ttl_category=data.get("ttl_category", "general"),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", data["created_at"]),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SemanticCacheManager
# ─────────────────────────────────────────────────────────────────────────────

class SemanticCacheManager:
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.backend_type = "in_memory"
        self._memory_store: dict[str, CachedItem] = {}
        self._hits = 0
        self._misses = 0
        self._init_backend()

    def _init_backend(self):
        try:
            r = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2
            )
            r.ping()
            self.redis_client = r
            self.backend_type = "redis"
            logger.info("SemanticCache initialised with Redis backend.")
        except Exception as exc:
            if settings.USE_IN_MEMORY_FALLBACK:
                self.redis_client = None
                self.backend_type = "in_memory"
                logger.warning(
                    f"Could not connect to Redis ({exc}). Using In-Memory cache fallback."
                )
            else:
                raise

    # ─────────────────────────────────────────────────────────────────────────
    # Core public API
    # ─────────────────────────────────────────────────────────────────────────

    def find_similar(
        self,
        prompt: str,
        query_vector: np.ndarray,
        threshold: float | None = None,
    ) -> tuple[bool, CachedItem | None, float]:
        """
        Scan cached vectors and return the best cosine-similarity match.
        Returns: (is_hit, matched_item, similarity_score)
        """
        m = _metrics()
        sim_threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        items = self._get_active_items()

        best_score = -1.0
        best_match: CachedItem | None = None

        for item in items:
            score = embedder_service.cosine_similarity(query_vector, item.vector)
            if score > best_score:
                best_score = score
                best_match = item

        if best_score >= 0:
            m.CACHE_SIMILARITY_HISTOGRAM.observe(round(best_score, 4))

        if best_match and best_score >= sim_threshold:
            # Update access metadata
            best_match.touch()
            self._persist_item(best_match)

            self._record_hit()
            m.CACHE_HITS_TOTAL.inc()
            return True, best_match, round(best_score, 4)

        self._record_miss()
        m.CACHE_MISSES_TOTAL.inc()
        return False, None, round(max(0.0, best_score), 4) if best_score != -1.0 else 0.0

    def store(
        self,
        prompt: str,
        response: str,
        model: str,
        provider: str,
        vector: np.ndarray,
        tokens: int,
        ttl_seconds: int | None = None,
        ttl_category: str = "general",
    ) -> CachedItem:
        """
        Persist a new inference result.  Enforces CACHE_MAX_ENTRIES via LRU eviction.
        """
        m = _metrics()
        t0 = time.time()

        ttl = ttl_seconds if ttl_seconds is not None else settings.DEFAULT_CACHE_TTL_SECONDS
        entry_id = str(uuid.uuid4())

        item = CachedItem(
            entry_id=entry_id,
            prompt=prompt,
            response=response,
            model=model,
            provider=provider,
            vector=vector,
            tokens=tokens,
            created_at=time.time(),
            ttl_seconds=ttl,
            ttl_category=ttl_category,
            access_count=0,
            last_accessed=time.time(),
        )

        # Evict LRU entries if at capacity before adding new one
        self._maybe_evict()

        self._persist_item(item)
        m.CACHE_STORE_LATENCY_SECONDS.observe(time.time() - t0)
        m.CACHE_ENTRIES_GAUGE.inc()
        m.CACHE_TTL_ASSIGNED.observe(ttl)
        m.CACHE_TTL_CATEGORY_TOTAL.labels(category=ttl_category).inc()
        return item

    def warm_from_list(
        self,
        entries: list[dict[str, Any]],
        default_model: str = "nexus-mock-v1",
        default_provider: str = "mock",
    ) -> int:
        """
        Bulk-load (prompt, response) pairs into the cache without going through
        the LLM.  Used by the startup warmer and the POST /cache/warm endpoint.

        Each entry dict must have "prompt" and "response". Optional keys:
          model, provider, ttl_seconds, ttl_category.

        Returns the count of entries actually stored (skips duplicates above threshold).
        """
        from app.services.cache_ttl_policy import ttl_policy  # noqa: PLC0415

        m = _metrics()
        stored = 0

        # Batch-embed all prompts at once for efficiency
        prompts = [e["prompt"] for e in entries]
        vectors = embedder_service.embed_batch(prompts)

        for entry, vec in zip(entries, vectors):
            prompt = entry["prompt"]
            # Skip if a sufficiently similar entry already exists
            is_hit, _, _ = self.find_similar(prompt, vec)
            if is_hit:
                continue

            decision = ttl_policy.decide(prompt)
            ttl = entry.get("ttl_seconds") or decision.ttl_seconds
            category = entry.get("ttl_category") or decision.category

            self.store(
                prompt=prompt,
                response=entry["response"],
                model=entry.get("model", default_model),
                provider=entry.get("provider", default_provider),
                vector=vec,
                tokens=len(prompt.split()) + len(entry["response"].split()),
                ttl_seconds=ttl,
                ttl_category=category,
            )
            stored += 1

        m.CACHE_WARMUP_ENTRIES_TOTAL.inc(stored)
        return stored

    def evict_entry(self, entry_id: str) -> bool:
        """
        Remove a single entry by id.
        Returns True if the entry existed and was removed, False otherwise.
        """
        m = _metrics()

        if self.redis_client:
            try:
                key = f"nexus:cache:item:{entry_id}"
                deleted = self.redis_client.delete(key)
                self.redis_client.srem("nexus:cache:active_keys", entry_id)
                if deleted:
                    m.CACHE_ENTRIES_GAUGE.dec()
                    m.CACHE_EVICTIONS_TOTAL.inc()
                return bool(deleted)
            except Exception as exc:
                logger.error(f"Redis evict error: {exc}")

        if entry_id in self._memory_store:
            del self._memory_store[entry_id]
            m.CACHE_ENTRIES_GAUGE.dec()
            m.CACHE_EVICTIONS_TOTAL.inc()
            return True
        return False

    def get_entry(self, entry_id: str) -> CachedItem | None:
        """Retrieve a full CachedItem by id (for the inspect endpoint)."""
        if self.redis_client:
            try:
                data = self.redis_client.get(f"nexus:cache:item:{entry_id}")
                if data:
                    return CachedItem.from_dict(json.loads(data))
                return None
            except Exception as exc:
                logger.error(f"Redis get_entry error: {exc}")

        return self._memory_store.get(entry_id)

    def get_stats(self) -> dict[str, Any]:
        active_items = self._get_active_items()
        m = _metrics()

        if self.redis_client:
            try:
                hits   = int(self.redis_client.get("nexus:stats:hits")   or 0)
                misses = int(self.redis_client.get("nexus:stats:misses") or 0)
            except Exception:
                hits, misses = self._hits, self._misses
        else:
            hits, misses = self._hits, self._misses

        total_requests = hits + misses
        ratio = round((hits / total_requests) * 100, 2) if total_requests > 0 else 0.0

        now = time.time()

        # Sample access-count histogram on every stats call
        for item in active_items:
            if item.access_count > 0:
                m.CACHE_ACCESS_COUNT.observe(item.access_count)

        # Sort by access_count desc for "top entries" view
        sorted_items = sorted(active_items, key=lambda x: x.access_count, reverse=True)

        entries_info = [
            {
                "id":               item.entry_id,
                "prompt":           item.prompt,
                "response_preview": item.response[:120] + ("..." if len(item.response) > 120 else ""),
                "created_at":       item.created_at,
                "expires_in_seconds": max(0, int(item.ttl_seconds - (now - item.created_at))),
                "ttl_category":     item.ttl_category,
                "access_count":     item.access_count,
                "last_accessed":    item.last_accessed,
            }
            for item in sorted_items
        ]

        # TTL category breakdown
        category_counts: dict[str, int] = {}
        for item in active_items:
            category_counts[item.ttl_category] = category_counts.get(item.ttl_category, 0) + 1

        m.CACHE_ENTRIES_GAUGE.set(len(active_items))

        return {
            "total_entries":     len(active_items),
            "hits":              hits,
            "misses":            misses,
            "hit_ratio":         ratio,
            "storage_backend":   self.backend_type,
            "max_entries":       settings.CACHE_MAX_ENTRIES,
            "entries":           entries_info,
            "ttl_category_counts": category_counts,
        }

    def clear_all(self) -> int:
        m = _metrics()
        count = 0
        if self.redis_client:
            try:
                key_ids = self.redis_client.smembers("nexus:cache:active_keys")
                count = len(key_ids)
                for eid in key_ids:
                    self.redis_client.delete(f"nexus:cache:item:{eid}")
                self.redis_client.delete("nexus:cache:active_keys")
                self.redis_client.delete("nexus:stats:hits")
                self.redis_client.delete("nexus:stats:misses")
            except Exception as exc:
                logger.error(f"Error clearing Redis cache: {exc}")

        mem_count = len(self._memory_store)
        self._memory_store.clear()
        self._hits = 0
        self._misses = 0
        m.CACHE_ENTRIES_GAUGE.set(0)
        return max(count, mem_count)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _persist_item(self, item: CachedItem) -> None:
        """Write (or overwrite) a single item to the active backend."""
        remaining_ttl = max(1, int(item.ttl_seconds - (time.time() - item.created_at)))
        if self.redis_client:
            try:
                key = f"nexus:cache:item:{item.entry_id}"
                self.redis_client.setex(key, remaining_ttl, json.dumps(item.to_dict()))
                self.redis_client.sadd("nexus:cache:active_keys", item.entry_id)
                return
            except Exception as exc:
                logger.error(f"Redis persist error: {exc}. Writing to memory fallback.")
        self._memory_store[item.entry_id] = item

    def _maybe_evict(self) -> None:
        """
        If the cache is at or above CACHE_MAX_ENTRIES, evict the least-recently-
        accessed entry to make room.  Runs in O(n) — acceptable for ≤ 500 entries.
        """
        items = self._get_active_items()
        if len(items) < settings.CACHE_MAX_ENTRIES:
            return

        # Find LRU entry (lowest last_accessed)
        lru = min(items, key=lambda x: x.last_accessed)
        logger.info(
            f"Cache at capacity ({len(items)}/{settings.CACHE_MAX_ENTRIES}). "
            f"Evicting LRU entry {lru.entry_id[:8]}… (last accessed "
            f"{time.time() - lru.last_accessed:.0f}s ago)"
        )
        self.evict_entry(lru.entry_id)

    def _get_active_items(self) -> list[CachedItem]:
        active: list[CachedItem] = []

        if self.redis_client:
            try:
                key_ids = self.redis_client.smembers("nexus:cache:active_keys")
                expired_keys = []
                for entry_id in key_ids:
                    data = self.redis_client.get(f"nexus:cache:item:{entry_id}")
                    if data:
                        active.append(CachedItem.from_dict(json.loads(data)))
                    else:
                        expired_keys.append(entry_id)
                if expired_keys:
                    self.redis_client.srem("nexus:cache:active_keys", *expired_keys)
                    # Adjust gauge for naturally-expired entries
                    _metrics().CACHE_ENTRIES_GAUGE.dec(len(expired_keys))
                return active
            except Exception as exc:
                logger.error(f"Redis read error: {exc}. Falling back to memory store.")

        # In-memory: prune expired
        expired_ids = [eid for eid, item in self._memory_store.items() if item.is_expired()]
        for eid in expired_ids:
            del self._memory_store[eid]
        if expired_ids:
            _metrics().CACHE_ENTRIES_GAUGE.dec(len(expired_ids))

        return list(self._memory_store.values())

    def _record_hit(self):
        if self.redis_client:
            try:
                self.redis_client.incr("nexus:stats:hits")
                return
            except Exception:
                pass
        self._hits += 1

    def _record_miss(self):
        if self.redis_client:
            try:
                self.redis_client.incr("nexus:stats:misses")
                return
            except Exception:
                pass
        self._misses += 1


semantic_cache = SemanticCacheManager()
