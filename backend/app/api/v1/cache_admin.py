import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import verify_api_key
from app.schemas.inference import (
    CacheClearResponse,
    CacheEvictResponse,
    CacheInspectResponse,
    CacheStatsResponse,
    CacheWarmRequest,
    CacheWarmResponse,
)
from app.services.semantic_cache import semantic_cache

router = APIRouter(prefix="/cache", tags=["Cache Management"])


# ── Existing endpoints ────────────────────────────────────────────────────────

@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(api_key: str = Depends(verify_api_key)):
    """
    Returns real-time semantic cache metrics: hit/miss counters, active stored
    entries (sorted by access count), adaptive TTL category breakdown, and the
    active storage backend.
    """
    stats = semantic_cache.get_stats()
    return CacheStatsResponse(**stats)


@router.delete("/clear", response_model=CacheClearResponse)
async def clear_cache(api_key: str = Depends(verify_api_key)):
    """Purges all cached embeddings and responses from Redis / memory store."""
    cleared = semantic_cache.clear_all()
    return CacheClearResponse(
        cleared_entries=cleared,
        status="success",
        message=f"Flushed {cleared} entries from semantic cache.",
    )


# ── New Option-3 endpoints ────────────────────────────────────────────────────

@router.post("/warm", response_model=CacheWarmResponse)
async def warm_cache(
    body: CacheWarmRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Trigger a manual cache warm-up.

    Generates LLM responses for each seed prompt and pre-populates the
    semantic cache with adaptive TTL.  Skips prompts that already have a
    sufficiently similar entry (cosine >= threshold) to avoid duplication.

    Useful after a cache flush or when deploying with a new model.
    """
    from app.services.cache_warming import run_warmup  # noqa: PLC0415

    result = await run_warmup(
        queries=body.queries,
        provider=body.provider,
        model=body.model,
    )
    return CacheWarmResponse(**result)


@router.delete("/evict/{entry_id}", response_model=CacheEvictResponse)
async def evict_entry(
    entry_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Remove a single cache entry by its UUID.

    Returns 404 if the entry does not exist (or has already expired).
    Use `GET /cache/stats` to browse entry IDs.
    """
    evicted = semantic_cache.evict_entry(entry_id)
    if not evicted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cache entry '{entry_id}' not found.",
        )
    return CacheEvictResponse(
        entry_id=entry_id,
        evicted=True,
        message="Entry successfully removed from cache.",
    )


@router.get("/inspect/{entry_id}", response_model=CacheInspectResponse)
async def inspect_entry(
    entry_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Retrieve full details of a single cache entry including the complete
    response text, adaptive TTL category, access count, and remaining TTL.

    Returns 404 if the entry does not exist or has expired.
    """
    item = semantic_cache.get_entry(entry_id)
    if item is None or item.is_expired():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cache entry '{entry_id}' not found or has expired.",
        )

    now = time.time()
    return CacheInspectResponse(
        entry_id=item.entry_id,
        prompt=item.prompt,
        response=item.response,
        model=item.model,
        provider=item.provider,
        created_at=item.created_at,
        ttl_seconds=item.ttl_seconds,
        ttl_category=item.ttl_category,
        expires_in_seconds=max(0, int(item.ttl_seconds - (now - item.created_at))),
        access_count=item.access_count,
        last_accessed=item.last_accessed,
        tokens=item.tokens,
    )
