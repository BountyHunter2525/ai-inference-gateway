"""
API Key Store
=============
Manages per-key metadata, daily usage counters, and tenant isolation.

Storage layout (Redis):
  nexus:keys:{key}          — JSON blob with key metadata
  nexus:keys:index          — Redis Set of all registered key values
  nexus:usage:{key}:{date}  — Hash with daily {requests, tokens} counters (TTL 48 h)

In-memory fallback mirrors the same structure with dicts.

Roles
-----
  admin   — full access including /admin/* endpoints
  user    — standard inference + cache access (default)
  readonly — only GET endpoints; no inference writes

Quota enforcement
-----------------
  QUOTA_DAILY_REQUESTS / QUOTA_DAILY_TOKENS from Settings are the defaults.
  Each key can override these via its own quota_requests / quota_tokens fields.
  0 means unlimited.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# ── lazy Redis access (avoids circular import with semantic_cache) ─────────────
def _redis():
    try:
        from app.services.semantic_cache import semantic_cache  # noqa: PLC0415
        return semantic_cache.redis_client
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# KeyMetadata dataclass
# ─────────────────────────────────────────────────────────────────────────────

class KeyMetadata:
    __slots__ = (
        "key", "name", "role", "tenant_id",
        "quota_requests", "quota_tokens",
        "created_at", "is_active", "description",
    )

    def __init__(
        self,
        key: str,
        name: str,
        role: str = "user",
        tenant_id: str = "default",
        quota_requests: int | None = None,
        quota_tokens: int | None = None,
        created_at: float | None = None,
        is_active: bool = True,
        description: str = "",
    ):
        self.key = key
        self.name = name
        self.role = role
        self.tenant_id = tenant_id
        self.quota_requests = quota_requests if quota_requests is not None else settings.QUOTA_DAILY_REQUESTS
        self.quota_tokens = quota_tokens if quota_tokens is not None else settings.QUOTA_DAILY_TOKENS
        self.created_at = created_at or time.time()
        self.is_active = is_active
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        return {
            "key":             self.key,
            "name":            self.name,
            "role":            self.role,
            "tenant_id":       self.tenant_id,
            "quota_requests":  self.quota_requests,
            "quota_tokens":    self.quota_tokens,
            "created_at":      self.created_at,
            "is_active":       self.is_active,
            "description":     self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__slots__})


# ─────────────────────────────────────────────────────────────────────────────
# KeyStore
# ─────────────────────────────────────────────────────────────────────────────

class KeyStore:
    """
    Dual-backend (Redis + in-memory fallback) API key registry.
    Thread-safe for in-memory paths; Redis operations are atomic via pipelines.
    """

    def __init__(self):
        # In-memory store: key → KeyMetadata
        self._store: dict[str, KeyMetadata] = {}
        self._seed_builtin_keys()

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _seed_builtin_keys(self) -> None:
        """Seed the two built-in keys from config so they have full metadata."""
        builtins = [
            KeyMetadata(
                key="sk-nexus-dev-demo-key",
                name="Dev Demo Key",
                role="user",
                tenant_id="demo",
                description="Built-in development key for playground use.",
            ),
            KeyMetadata(
                key="sk-test-client-123",
                name="Test Client",
                role="user",
                tenant_id="demo",
                description="Built-in test client key.",
            ),
            KeyMetadata(
                key=settings.ADMIN_API_KEY,
                name="Master Admin Key",
                role="admin",
                tenant_id="system",
                quota_requests=0,   # unlimited
                quota_tokens=0,
                description="Master admin key — full system access.",
            ),
        ]
        for meta in builtins:
            self._store[meta.key] = meta
            self._persist_key(meta)

    # ── Key CRUD ──────────────────────────────────────────────────────────────

    def create_key(
        self,
        name: str,
        role: str = "user",
        tenant_id: str = "default",
        quota_requests: int | None = None,
        quota_tokens: int | None = None,
        description: str = "",
    ) -> KeyMetadata:
        """Generate a new API key with the given metadata and persist it."""
        raw = secrets.token_urlsafe(32)
        key = f"sk-nexus-{raw[:40]}"
        meta = KeyMetadata(
            key=key,
            name=name,
            role=role,
            tenant_id=tenant_id,
            quota_requests=quota_requests,
            quota_tokens=quota_tokens,
            description=description,
        )
        self._store[key] = meta
        self._persist_key(meta)

        try:
            from app.services.metrics import ENTERPRISE_ACTIVE_KEYS_GAUGE  # noqa: PLC0415
            ENTERPRISE_ACTIVE_KEYS_GAUGE.inc()
        except Exception:
            pass

        logger.info(f"Created API key '{key[:16]}…' for tenant '{tenant_id}' (role={role})")
        return meta

    def get_key(self, key: str) -> KeyMetadata | None:
        """Look up metadata for a key. Returns None if not found or revoked."""
        # Check in-memory first
        meta = self._store.get(key)
        if meta is not None:
            return meta if meta.is_active else None

        # Try Redis
        r = _redis()
        if r:
            try:
                raw = r.get(f"nexus:keys:{key}")
                if raw:
                    meta = KeyMetadata.from_dict(json.loads(raw))
                    self._store[key] = meta   # warm the local cache
                    return meta if meta.is_active else None
            except Exception as exc:
                logger.error(f"KeyStore Redis get error: {exc}")
        return None

    def list_keys(self, tenant_id: str | None = None) -> list[KeyMetadata]:
        """List all active keys, optionally filtered by tenant_id."""
        keys = self._load_all_keys()
        if tenant_id:
            keys = [k for k in keys if k.tenant_id == tenant_id]
        return [k for k in keys if k.is_active]

    def revoke_key(self, key: str) -> bool:
        """Soft-delete a key by marking it inactive."""
        meta = self.get_key(key)
        if meta is None:
            return False
        meta.is_active = False
        self._store[key] = meta
        self._persist_key(meta)

        try:
            from app.services.metrics import ENTERPRISE_ACTIVE_KEYS_GAUGE  # noqa: PLC0415
            ENTERPRISE_ACTIVE_KEYS_GAUGE.dec()
        except Exception:
            pass

        logger.info(f"Revoked API key '{key[:16]}…'")
        return True

    def is_valid(self, key: str) -> bool:
        """Return True if the key exists and is active."""
        return self.get_key(key) is not None

    # ── Daily usage counters ──────────────────────────────────────────────────

    def _usage_key(self, key: str) -> str:
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        return f"nexus:usage:{key}:{date_str}"

    def record_usage(self, key: str, tokens: int = 0) -> None:
        """Increment today's request + token counters for a key."""
        r = _redis()
        if r:
            try:
                ukey = self._usage_key(key)
                pipe = r.pipeline()
                pipe.hincrby(ukey, "requests", 1)
                pipe.hincrby(ukey, "tokens", tokens)
                pipe.expire(ukey, 172800)   # 48 h TTL
                pipe.execute()
                return
            except Exception as exc:
                logger.error(f"KeyStore usage record Redis error: {exc}")

        # In-memory fallback
        ukey = self._usage_key(key)
        if ukey not in self._store:
            # Store daily counters as a special KeyMetadata-free dict
            self._store[ukey] = {"requests": 0, "tokens": 0}  # type: ignore[assignment]
        bucket = self._store[ukey]  # type: ignore[assignment]
        bucket["requests"] = bucket.get("requests", 0) + 1
        bucket["tokens"]   = bucket.get("tokens",   0) + tokens

    def get_usage(self, key: str) -> dict[str, int]:
        """Return today's {requests, tokens} usage for a key."""
        r = _redis()
        if r:
            try:
                ukey = self._usage_key(key)
                data = r.hgetall(ukey)
                return {
                    "requests": int(data.get("requests", 0)),
                    "tokens":   int(data.get("tokens",   0)),
                }
            except Exception as exc:
                logger.error(f"KeyStore usage get Redis error: {exc}")

        ukey = self._usage_key(key)
        bucket = self._store.get(ukey, {})  # type: ignore[arg-type]
        return {
            "requests": bucket.get("requests", 0),   # type: ignore[union-attr]
            "tokens":   bucket.get("tokens",   0),   # type: ignore[union-attr]
        }

    def check_quota(self, key: str) -> tuple[bool, dict[str, Any]]:
        """
        Check whether this key is within its daily quota.

        Returns (within_quota, usage_info_dict).
        usage_info contains: requests_used, requests_limit, tokens_used, tokens_limit,
        requests_remaining, tokens_remaining.
        """
        meta = self.get_key(key)
        if meta is None:
            return False, {}

        usage = self.get_usage(key)
        req_used   = usage["requests"]
        tok_used   = usage["tokens"]
        req_limit  = meta.quota_requests   # 0 = unlimited
        tok_limit  = meta.quota_tokens

        req_ok = (req_limit == 0) or (req_used < req_limit)
        tok_ok = (tok_limit == 0) or (tok_used < tok_limit)

        info = {
            "requests_used":      req_used,
            "requests_limit":     req_limit,
            "requests_remaining": max(0, req_limit - req_used) if req_limit else -1,
            "tokens_used":        tok_used,
            "tokens_limit":       tok_limit,
            "tokens_remaining":   max(0, tok_limit - tok_used) if tok_limit else -1,
            "tenant_id":          meta.tenant_id,
            "role":               meta.role,
        }
        return (req_ok and tok_ok), info

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _persist_key(self, meta: KeyMetadata) -> None:
        r = _redis()
        if r:
            try:
                r.set(f"nexus:keys:{meta.key}", json.dumps(meta.to_dict()))
                r.sadd("nexus:keys:index", meta.key)
            except Exception as exc:
                logger.error(f"KeyStore persist Redis error: {exc}")

    def _load_all_keys(self) -> list[KeyMetadata]:
        r = _redis()
        if r:
            try:
                all_keys = r.smembers("nexus:keys:index")
                result = []
                for k in all_keys:
                    raw = r.get(f"nexus:keys:{k}")
                    if raw:
                        result.append(KeyMetadata.from_dict(json.loads(raw)))
                return result
            except Exception as exc:
                logger.error(f"KeyStore load_all Redis error: {exc}")

        return [v for v in self._store.values() if isinstance(v, KeyMetadata)]


key_store = KeyStore()
