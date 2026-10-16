import logging
import time
from typing import Dict, List, Tuple

from app.config import settings
from app.services.semantic_cache import semantic_cache

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    def __init__(self):
        self._memory_windows: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> tuple[bool, int, int]:
        """
        Sliding window rate limit checker.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_size = settings.RATE_LIMIT_WINDOW_SECONDS
        max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        window_start = now - window_size

        redis_client = semantic_cache.redis_client
        if redis_client:
            try:
                key = f"nexus:ratelimit:{identifier}"
                pipe = redis_client.pipeline()
                # Remove timestamps older than window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count current timestamps in window
                pipe.zcard(key)
                # Add current request timestamp
                pipe.zadd(key, {str(now): now})
                # Set TTL on key
                pipe.expire(key, window_size)
                results = pipe.execute()

                current_count = results[1]
                if current_count >= max_requests:
                    return False, 0, int(window_size)

                remaining = max(0, max_requests - (current_count + 1))
                return True, remaining, 0
            except Exception as e:
                logger.error(f"Redis rate limiter error: {e}. Falling back to memory.")

        # In-Memory Sliding Window
        timestamps = self._memory_windows.get(identifier, [])
        # Prune old timestamps
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= max_requests:
            oldest = timestamps[0] if timestamps else now
            retry_after = max(1, int(window_size - (now - oldest)))
            self._memory_windows[identifier] = timestamps
            return False, 0, retry_after

        timestamps.append(now)
        self._memory_windows[identifier] = timestamps
        remaining = max(0, max_requests - len(timestamps))
        return True, remaining, 0


rate_limiter = SlidingWindowRateLimiter()
