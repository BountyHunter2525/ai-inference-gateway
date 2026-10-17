"""
Cache Warming Service
======================
Runs on application startup (via FastAPI lifespan) and when triggered
manually via POST /api/v1/cache/warm.

Workflow:
  1. Read seed prompts from settings.warm_queries_list
  2. Batch-embed them all in one sentence-transformers call
  3. Run each through the Mock LLM to generate a deterministic response
  4. Store results in the cache with adaptive TTL via CacheTTLPolicy
  5. Record Prometheus metrics for every run

The warmer is intentionally async and non-blocking — it yields between
items so the HTTP server keeps accepting requests during the warm-up.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


async def run_warmup(
    *,
    queries: list[str] | None = None,
    provider: str = "mock",
    model: str = "nexus-mock-v1",
) -> dict[str, Any]:
    """
    Execute a cache warm-up pass.

    Args:
        queries:  List of prompts to pre-cache.  Defaults to settings.warm_queries_list.
        provider: LLM provider to use for generating mock responses.
        model:    Model name tag to store with each entry.

    Returns a summary dict suitable for API responses.
    """
    # Late imports to avoid circular dependencies at module load time
    from app.services.cache_ttl_policy import ttl_policy  # noqa: PLC0415
    from app.services.llm_provider import llm_service  # noqa: PLC0415
    from app.services.metrics import (  # noqa: PLC0415
        CACHE_WARMUP_ENTRIES_TOTAL,
        CACHE_WARMUP_RUNS_TOTAL,
    )
    from app.services.semantic_cache import semantic_cache  # noqa: PLC0415

    seed_queries = queries or settings.warm_queries_list
    if not seed_queries:
        logger.info("Cache warming: no seed queries configured, skipping.")
        return {"status": "skipped", "reason": "no queries configured", "stored": 0}

    CACHE_WARMUP_RUNS_TOTAL.inc()
    t0 = time.time()
    stored = 0
    skipped = 0

    logger.info(f"Cache warming started — {len(seed_queries)} seed queries.")

    entries: list[dict[str, Any]] = []
    for prompt in seed_queries:
        try:
            # Generate response via LLM service (uses mock by default — instant)
            text, tokens, model_used, provider_used = await llm_service.execute_inference(
                prompt=prompt,
                provider_name=provider,
                model_name=model,
                max_tokens=256,
                temperature=0.0,  # deterministic for cache seeding
            )
            decision = ttl_policy.decide(prompt)
            entries.append({
                "prompt":       prompt,
                "response":     text,
                "model":        model_used,
                "provider":     provider_used,
                "ttl_seconds":  decision.ttl_seconds,
                "ttl_category": decision.category,
            })
        except Exception as exc:
            logger.warning(f"Warm-up: failed to generate response for {prompt!r}: {exc}")
            skipped += 1

        # Yield control so the event loop stays responsive
        await asyncio.sleep(0)

    # Bulk-store all generated entries (skips existing near-duplicates)
    if entries:
        stored = semantic_cache.warm_from_list(entries)
        CACHE_WARMUP_ENTRIES_TOTAL.inc(stored)

    elapsed = round((time.time() - t0) * 1000, 1)
    logger.info(
        f"Cache warming complete — stored {stored}, skipped {skipped}, "
        f"elapsed {elapsed} ms."
    )

    return {
        "status":         "ok",
        "queries_attempted": len(seed_queries),
        "stored":         stored,
        "skipped_errors": skipped,
        "elapsed_ms":     elapsed,
    }


async def startup_warmup() -> None:
    """
    Called from the FastAPI lifespan event on application start.
    Silently skips if CACHE_WARMING_ENABLED is False.
    """
    if not settings.CACHE_WARMING_ENABLED:
        logger.info("Cache warming disabled (CACHE_WARMING_ENABLED=False).")
        return
    try:
        result = await run_warmup()
        logger.info(f"Startup warm-up result: {result}")
    except Exception as exc:
        # Never crash startup due to a warming failure
        logger.error(f"Startup warm-up failed (non-fatal): {exc}")
