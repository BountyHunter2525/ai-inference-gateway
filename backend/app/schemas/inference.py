import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The input prompt for the AI model")
    model: str | None = Field(None, description="Model identifier override")
    provider: str | None = Field(None, description="Provider override: 'mock', 'huggingface', 'openai'")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(256, ge=1, le=4096)
    bypass_cache: bool | None = Field(False, description="Force fresh inference, bypassing cache")
    custom_ttl_seconds: int | None = Field(None, description="Custom TTL for this response if cached")


class InferenceResponse(BaseModel):
    prompt: str
    response: str
    model: str
    provider: str
    cache_hit: bool
    similarity_score: float | None = None
    latency_ms: float
    tokens_used: int
    bypassed_due_to_volatility: bool = False
    ttl_category: str | None = None          # "factual" | "technical" | "general" | None on hit
    timestamp: float = Field(default_factory=time.time)


class CacheEntryInfo(BaseModel):
    id: str
    prompt: str
    response_preview: str
    created_at: float
    expires_in_seconds: float
    ttl_category: str = "general"            # adaptive TTL category
    access_count: int = 0                    # how many times this entry was served
    last_accessed: float | None = None       # unix timestamp of last cache hit


class CacheStatsResponse(BaseModel):
    total_entries: int
    hits: int
    misses: int
    hit_ratio: float
    storage_backend: str
    max_entries: int = 500
    entries: list[CacheEntryInfo] = []
    ttl_category_counts: dict[str, int] = {}  # {"factual": 3, "technical": 5, ...}


class CacheClearResponse(BaseModel):
    cleared_entries: int
    status: str
    message: str


# ── New Option-3 response schemas ─────────────────────────────────────────────

class CacheWarmRequest(BaseModel):
    """Body for POST /cache/warm — optionally supply custom seed prompts."""
    queries: list[str] | None = Field(
        None,
        description="Custom prompts to warm. Defaults to the server-configured seed list.",
    )
    provider: str = Field("mock", description="Provider to use for generating responses.")
    model: str = Field("nexus-mock-v1", description="Model name tag.")


class CacheWarmResponse(BaseModel):
    status: str
    queries_attempted: int
    stored: int
    skipped_errors: int
    elapsed_ms: float


class CacheEvictResponse(BaseModel):
    entry_id: str
    evicted: bool
    message: str


class CacheInspectResponse(BaseModel):
    entry_id: str
    prompt: str
    response: str
    model: str
    provider: str
    created_at: float
    ttl_seconds: int
    ttl_category: str
    expires_in_seconds: int
    access_count: int
    last_accessed: float
    tokens: int


class HealthResponse(BaseModel):
    status: str
    version: str
    backend_storage: str
    default_provider: str
    embedder_ready: bool
