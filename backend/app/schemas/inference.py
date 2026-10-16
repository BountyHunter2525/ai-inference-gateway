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
    timestamp: float = Field(default_factory=time.time)


class CacheEntryInfo(BaseModel):
    id: str
    prompt: str
    response_preview: str
    created_at: float
    expires_in_seconds: float


class CacheStatsResponse(BaseModel):
    total_entries: int
    hits: int
    misses: int
    hit_ratio: float
    storage_backend: str
    entries: list[CacheEntryInfo] = []


class CacheClearResponse(BaseModel):
    cleared_entries: int
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    backend_storage: str
    default_provider: str
    embedder_ready: bool
