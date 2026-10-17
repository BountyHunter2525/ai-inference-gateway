import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Inference
# ─────────────────────────────────────────────────────────────────────────────

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
    ttl_category: str | None = None
    tenant_id: str | None = None
    timestamp: float = Field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────────────────────

class CacheEntryInfo(BaseModel):
    id: str
    prompt: str
    response_preview: str
    created_at: float
    expires_in_seconds: float
    ttl_category: str = "general"
    access_count: int = 0
    last_accessed: float | None = None


class CacheStatsResponse(BaseModel):
    total_entries: int
    hits: int
    misses: int
    hit_ratio: float
    storage_backend: str
    max_entries: int = 500
    entries: list[CacheEntryInfo] = []
    ttl_category_counts: dict[str, int] = {}


class CacheClearResponse(BaseModel):
    cleared_entries: int
    status: str
    message: str


class CacheWarmRequest(BaseModel):
    queries: list[str] | None = Field(None)
    provider: str = Field("mock")
    model: str = Field("nexus-mock-v1")


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


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    backend_storage: str
    default_provider: str
    embedder_ready: bool


# ─────────────────────────────────────────────────────────────────────────────
# Enterprise — Option 4
# ─────────────────────────────────────────────────────────────────────────────

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Human-readable label for this key")
    role: str = Field("user", description="Role: 'user' | 'admin' | 'readonly'")
    tenant_id: str = Field("default", description="Tenant namespace for cache isolation")
    quota_requests: int | None = Field(None, description="Daily request quota (None = use default)")
    quota_tokens: int | None = Field(None, description="Daily token quota (None = use default)")
    description: str = Field("", description="Optional description")


class ApiKeyResponse(BaseModel):
    key: str
    name: str
    role: str
    tenant_id: str
    quota_requests: int
    quota_tokens: int
    description: str
    created_at: float
    is_active: bool


class ApiKeyUsage(BaseModel):
    key_preview: str        # first 16 chars + "…"
    name: str
    tenant_id: str
    role: str
    requests_used: int
    requests_limit: int     # 0 = unlimited
    requests_remaining: int # -1 = unlimited
    tokens_used: int
    tokens_limit: int
    tokens_remaining: int
    quota_pct_requests: float   # 0.0–100.0
    quota_pct_tokens: float
    is_active: bool


class AuditLogEntry(BaseModel):
    event_id: str
    timestamp: float
    event_type: str
    api_key: str        # masked
    tenant_id: str
    endpoint: str
    method: str
    status_code: int
    detail: str
    latency_ms: float | None = None


class AuditLogResponse(BaseModel):
    entries: list[AuditLogEntry]
    total_returned: int


class AdminStatsResponse(BaseModel):
    total_active_keys: int
    total_tenants: int
    audit_events_today: int
    keys: list[ApiKeyUsage]
