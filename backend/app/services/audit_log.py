"""
Audit Log Service
==================
Writes structured audit events to Redis (LIST with LTRIM) or in-memory fallback.

Every event is a JSON object with:
  event_id    — UUID
  timestamp   — Unix float
  event_type  — "inference" | "cache_clear" | "key_created" | "key_revoked" |
                "cache_warm" | "quota_exceeded" | "auth_failed" | "admin_action"
  api_key     — masked (first 12 chars + "…")
  tenant_id   — tenant namespace
  endpoint    — HTTP path
  method      — HTTP verb
  status_code — HTTP response code
  detail      — free-form string with extra context
  latency_ms  — optional float

Redis layout:
  nexus:audit:log  — LPUSH (newest first), LTRIMmed to AUDIT_LOG_MAX_ENTRIES * 10
  TTL not set on the list itself; entries are naturally pruned by LTRIM.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback
_memory_log: list[dict[str, Any]] = []
_REDIS_KEY = "nexus:audit:log"
_MAX_REDIS_ENTRIES = settings.AUDIT_LOG_MAX_ENTRIES * 10   # store more in Redis, trim on read


def _redis():
    try:
        from app.services.semantic_cache import semantic_cache  # noqa: PLC0415
        return semantic_cache.redis_client
    except Exception:
        return None


def _mask_key(key: str) -> str:
    return key[:12] + "…" if len(key) > 12 else key


def log_event(
    event_type: str,
    api_key: str = "",
    tenant_id: str = "unknown",
    endpoint: str = "",
    method: str = "",
    status_code: int = 200,
    detail: str = "",
    latency_ms: float | None = None,
) -> None:
    """
    Append one audit event. Fire-and-forget — never raises.
    Call from anywhere; it is intentionally synchronous and fast.
    """
    try:
        event: dict[str, Any] = {
            "event_id":    str(uuid.uuid4()),
            "timestamp":   round(time.time(), 3),
            "event_type":  event_type,
            "api_key":     _mask_key(api_key) if api_key else "",
            "tenant_id":   tenant_id,
            "endpoint":    endpoint,
            "method":      method,
            "status_code": status_code,
            "detail":      detail,
        }
        if latency_ms is not None:
            event["latency_ms"] = round(latency_ms, 2)

        raw = json.dumps(event)

        r = _redis()
        if r:
            try:
                r.lpush(_REDIS_KEY, raw)
                r.ltrim(_REDIS_KEY, 0, _MAX_REDIS_ENTRIES - 1)
                return
            except Exception as exc:
                logger.debug(f"Audit log Redis write failed: {exc}. Falling back to memory.")

        # In-memory fallback — prepend (newest first) and trim
        _memory_log.insert(0, event)
        if len(_memory_log) > _MAX_REDIS_ENTRIES:
            del _memory_log[_MAX_REDIS_ENTRIES:]

        # Prometheus
        try:
            from app.services.metrics import ENTERPRISE_AUDIT_EVENTS_TOTAL  # noqa: PLC0415
            ENTERPRISE_AUDIT_EVENTS_TOTAL.labels(event_type=event_type).inc()
        except Exception:
            pass

    except Exception as exc:
        logger.error(f"Audit log error (non-fatal): {exc}")


def get_recent(
    limit: int | None = None,
    tenant_id: str | None = None,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve the most recent audit events, optionally filtered.
    Returns newest-first.
    """
    cap = min(limit or settings.AUDIT_LOG_MAX_ENTRIES, settings.AUDIT_LOG_MAX_ENTRIES)

    r = _redis()
    if r:
        try:
            raw_list = r.lrange(_REDIS_KEY, 0, _MAX_REDIS_ENTRIES - 1)
            events = [json.loads(r2) for r2 in raw_list]
        except Exception as exc:
            logger.error(f"Audit log Redis read error: {exc}")
            events = list(_memory_log)
    else:
        events = list(_memory_log)

    # Apply filters
    if tenant_id:
        events = [e for e in events if e.get("tenant_id") == tenant_id]
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return events[:cap]


def clear() -> int:
    """Remove all audit log entries. Returns count deleted."""
    count = 0
    r = _redis()
    if r:
        try:
            count = r.llen(_REDIS_KEY)
            r.delete(_REDIS_KEY)
        except Exception as exc:
            logger.error(f"Audit log clear Redis error: {exc}")
    mem_count = len(_memory_log)
    _memory_log.clear()
    return max(count, mem_count)
