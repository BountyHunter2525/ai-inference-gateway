import time
import json
import uuid
import logging
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import redis

from app.config import settings
from app.services.embedder import embedder_service

logger = logging.getLogger(__name__)


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
        ttl_seconds: int
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

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "provider": self.provider,
            "vector": self.vector.tolist(),
            "tokens": self.tokens,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedItem":
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
        )


class SemanticCacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.backend_type = "in_memory"
        self._memory_store: Dict[str, CachedItem] = {}
        self._hits = 0
        self._misses = 0
        self._init_backend()

    def _init_backend(self):
        try:
            r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            r.ping()
            self.redis_client = r
            self.backend_type = "redis"
            logger.info("SemanticCache initialized with Redis backend.")
        except Exception as e:
            if settings.USE_IN_MEMORY_FALLBACK:
                self.redis_client = None
                self.backend_type = "in_memory"
                logger.warning(f"Could not connect to Redis ({e}). Using In-Memory cache fallback.")
            else:
                raise

    def find_similar(
        self, 
        prompt: str, 
        query_vector: np.ndarray, 
        threshold: Optional[float] = None
    ) -> Tuple[bool, Optional[CachedItem], float]:
        """
        Scans cached vectors and calculates cosine similarity.
        Returns: (is_hit, matched_item, similarity_score)
        """
        sim_threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        items = self._get_active_items()

        best_score = -1.0
        best_match: Optional[CachedItem] = None

        for item in items:
            score = embedder_service.cosine_similarity(query_vector, item.vector)
            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= sim_threshold:
            self._record_hit()
            return True, best_match, round(best_score, 4)

        self._record_miss()
        return False, None, round(max(0.0, best_score), 4) if best_score != -1.0 else 0.0

    def store(
        self,
        prompt: str,
        response: str,
        model: str,
        provider: str,
        vector: np.ndarray,
        tokens: int,
        ttl_seconds: Optional[int] = None
    ) -> CachedItem:
        """
        Stores an inference response alongside its vector embedding and TTL.
        """
        entry_id = str(uuid.uuid4())
        ttl = ttl_seconds if ttl_seconds is not None else settings.DEFAULT_CACHE_TTL_SECONDS
        
        item = CachedItem(
            entry_id=entry_id,
            prompt=prompt,
            response=response,
            model=model,
            provider=provider,
            vector=vector,
            tokens=tokens,
            created_at=time.time(),
            ttl_seconds=ttl
        )

        if self.redis_client:
            try:
                key = f"nexus:cache:item:{entry_id}"
                self.redis_client.setex(key, ttl, json.dumps(item.to_dict()))
                self.redis_client.sadd("nexus:cache:active_keys", entry_id)
                return item
            except Exception as e:
                logger.error(f"Failed to write to Redis: {e}. Writing to memory fallback.")
        
        # Memory store fallback
        self._memory_store[entry_id] = item
        return item

    def _get_active_items(self) -> List[CachedItem]:
        active = []
        now = time.time()

        if self.redis_client:
            try:
                key_ids = self.redis_client.smembers("nexus:cache:active_keys")
                expired_keys = []
                for entry_id in key_ids:
                    key = f"nexus:cache:item:{entry_id}"
                    data = self.redis_client.get(key)
                    if data:
                        active.append(CachedItem.from_dict(json.loads(data)))
                    else:
                        expired_keys.append(entry_id)
                
                if expired_keys:
                    self.redis_client.srem("nexus:cache:active_keys", *expired_keys)
                return active
            except Exception as e:
                logger.error(f"Redis read error: {e}. Falling back to memory store.")

        # In-memory cleanup
        expired_ids = []
        for eid, item in self._memory_store.items():
            if item.is_expired():
                expired_ids.append(eid)
            else:
                active.append(item)
        for eid in expired_ids:
            del self._memory_store[eid]

        return active

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

    def get_stats(self) -> Dict[str, Any]:
        active_items = self._get_active_items()
        
        if self.redis_client:
            try:
                hits = int(self.redis_client.get("nexus:stats:hits") or 0)
                misses = int(self.redis_client.get("nexus:stats:misses") or 0)
            except Exception:
                hits, misses = self._hits, self._misses
        else:
            hits, misses = self._hits, self._misses

        total_requests = hits + misses
        ratio = round((hits / total_requests) * 100, 2) if total_requests > 0 else 0.0

        now = time.time()
        entries_info = [
            {
                "id": item.entry_id,
                "prompt": item.prompt,
                "response_preview": item.response[:120] + ("..." if len(item.response) > 120 else ""),
                "created_at": item.created_at,
                "expires_in_seconds": max(0, int(item.ttl_seconds - (now - item.created_at))),
            }
            for item in sorted(active_items, key=lambda x: x.created_at, reverse=True)
        ]

        return {
            "total_entries": len(active_items),
            "hits": hits,
            "misses": misses,
            "hit_ratio": ratio,
            "storage_backend": self.backend_type,
            "entries": entries_info
        }

    def clear_all(self) -> int:
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
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")

        mem_count = len(self._memory_store)
        self._memory_store.clear()
        self._hits = 0
        self._misses = 0
        return max(count, mem_count)


semantic_cache = SemanticCacheManager()
