from fastapi import APIRouter, Depends
from app.api.deps import verify_api_key
from app.schemas.inference import CacheStatsResponse, CacheClearResponse
from app.services.semantic_cache import semantic_cache

router = APIRouter(prefix="/cache", tags=["Cache Management"])


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(api_key: str = Depends(verify_api_key)):
    """
    Returns real-time semantic cache metrics, hit/miss counters, active stored entries, and storage backend.
    """
    stats = semantic_cache.get_stats()
    return CacheStatsResponse(**stats)


@router.delete("/clear", response_model=CacheClearResponse)
async def clear_cache(api_key: str = Depends(verify_api_key)):
    """
    Purges all cached embeddings and responses from Redis / memory store.
    """
    cleared = semantic_cache.clear_all()
    return CacheClearResponse(
        cleared_entries=cleared,
        status="success",
        message=f"Flushed {cleared} entries from semantic cache."
    )
