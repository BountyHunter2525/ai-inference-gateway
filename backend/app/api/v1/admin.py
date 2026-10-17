"""
Admin API — /api/v1/admin/*
============================
All endpoints require admin role (ADMIN_API_KEY or role='admin' key).

Endpoints:
  POST   /admin/keys              — create a new API key
  GET    /admin/keys              — list all keys with usage
  GET    /admin/keys/{key}/usage  — usage + quota detail for one key
  DELETE /admin/keys/{key}        — revoke a key
  GET    /admin/audit             — recent audit log (filterable)
  DELETE /admin/audit             — clear audit log
  GET    /admin/stats             — aggregate dashboard stats
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import verify_admin_key
from app.schemas.inference import (
    AdminStatsResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyUsage,
    AuditLogEntry,
    AuditLogResponse,
)

router = APIRouter(prefix="/admin", tags=["Enterprise Admin"])


# ── Key management ────────────────────────────────────────────────────────────

@router.post("/keys", response_model=ApiKeyResponse, status_code=201)
async def create_key(
    body: ApiKeyCreateRequest,
    admin_key: str = Depends(verify_admin_key),
):
    """
    Generate a new API key with the given role, tenant, and quota settings.
    The generated key value is only returned once — store it securely.
    """
    from app.services import audit_log  # noqa: PLC0415
    from app.services.key_store import key_store  # noqa: PLC0415

    meta = key_store.create_key(
        name=body.name,
        role=body.role,
        tenant_id=body.tenant_id,
        quota_requests=body.quota_requests,
        quota_tokens=body.quota_tokens,
        description=body.description,
    )
    audit_log.log_event(
        "key_created", api_key=admin_key,
        tenant_id=body.tenant_id, endpoint="/admin/keys",
        method="POST", detail=f"Created key '{meta.key[:16]}…' for '{body.name}'",
    )
    return ApiKeyResponse(**meta.to_dict())


@router.get("/keys", response_model=list[ApiKeyUsage])
async def list_keys(
    tenant_id: str | None = Query(None, description="Filter by tenant_id"),
    admin_key: str = Depends(verify_admin_key),
):
    """List all active API keys with today's usage and quota status."""
    from app.services.key_store import key_store  # noqa: PLC0415

    keys = key_store.list_keys(tenant_id=tenant_id)
    result = []
    for meta in keys:
        usage = key_store.get_usage(meta.key)
        req_used  = usage["requests"]
        tok_used  = usage["tokens"]
        req_limit = meta.quota_requests
        tok_limit = meta.quota_tokens
        result.append(ApiKeyUsage(
            key_preview=meta.key[:16] + "…",
            name=meta.name,
            tenant_id=meta.tenant_id,
            role=meta.role,
            requests_used=req_used,
            requests_limit=req_limit,
            requests_remaining=max(0, req_limit - req_used) if req_limit else -1,
            tokens_used=tok_used,
            tokens_limit=tok_limit,
            tokens_remaining=max(0, tok_limit - tok_used) if tok_limit else -1,
            quota_pct_requests=round((req_used / req_limit * 100), 1) if req_limit else 0.0,
            quota_pct_tokens=round((tok_used / tok_limit * 100), 1) if tok_limit else 0.0,
            is_active=meta.is_active,
        ))
    return result


@router.get("/keys/{key_id}/usage", response_model=ApiKeyUsage)
async def get_key_usage(
    key_id: str,
    admin_key: str = Depends(verify_admin_key),
):
    """Return detailed usage and quota info for a single key."""
    from app.services.key_store import key_store  # noqa: PLC0415

    meta = key_store.get_key(key_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Key '{key_id[:16]}…' not found.")

    usage = key_store.get_usage(key_id)
    req_used  = usage["requests"]
    tok_used  = usage["tokens"]
    req_limit = meta.quota_requests
    tok_limit = meta.quota_tokens
    return ApiKeyUsage(
        key_preview=meta.key[:16] + "…",
        name=meta.name,
        tenant_id=meta.tenant_id,
        role=meta.role,
        requests_used=req_used,
        requests_limit=req_limit,
        requests_remaining=max(0, req_limit - req_used) if req_limit else -1,
        tokens_used=tok_used,
        tokens_limit=tok_limit,
        tokens_remaining=max(0, tok_limit - tok_used) if tok_limit else -1,
        quota_pct_requests=round((req_used / req_limit * 100), 1) if req_limit else 0.0,
        quota_pct_tokens=round((tok_used / tok_limit * 100), 1) if tok_limit else 0.0,
        is_active=meta.is_active,
    )


@router.delete("/keys/{key_id}", status_code=200)
async def revoke_key(
    key_id: str,
    admin_key: str = Depends(verify_admin_key),
):
    """Soft-revoke an API key. The key will immediately stop working."""
    from app.services import audit_log  # noqa: PLC0415
    from app.services.key_store import key_store  # noqa: PLC0415

    if key_id == admin_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke the key currently being used for this request.",
        )
    revoked = key_store.revoke_key(key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail=f"Key '{key_id[:16]}…' not found.")

    audit_log.log_event(
        "key_revoked", api_key=admin_key,
        endpoint=f"/admin/keys/{key_id[:16]}",
        method="DELETE", detail=f"Revoked key '{key_id[:16]}…'",
    )
    return {"status": "revoked", "key_preview": key_id[:16] + "…", "message": "Key has been revoked."}


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=AuditLogResponse)
async def get_audit_log(
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    tenant_id: str | None = Query(None),
    event_type: str | None = Query(None, description="Filter by event type"),
    admin_key: str = Depends(verify_admin_key),
):
    """
    Retrieve recent audit log entries, newest first.
    Filter by tenant_id or event_type to narrow results.
    """
    from app.services import audit_log  # noqa: PLC0415

    entries = audit_log.get_recent(limit=limit, tenant_id=tenant_id, event_type=event_type)
    return AuditLogResponse(
        entries=[AuditLogEntry(**e) for e in entries],
        total_returned=len(entries),
    )


@router.delete("/audit", status_code=200)
async def clear_audit_log(admin_key: str = Depends(verify_admin_key)):
    """Permanently delete all audit log entries."""
    from app.services import audit_log  # noqa: PLC0415

    count = audit_log.clear()
    audit_log.log_event(
        "admin_action", api_key=admin_key,
        endpoint="/admin/audit", method="DELETE",
        detail=f"Cleared {count} audit log entries",
    )
    return {"status": "cleared", "entries_removed": count}


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(admin_key: str = Depends(verify_admin_key)):
    """
    Aggregate admin dashboard: total keys, tenants, audit volume, per-key usage.
    """
    from app.services import audit_log  # noqa: PLC0415
    from app.services.key_store import key_store  # noqa: PLC0415

    all_keys = key_store.list_keys()
    tenants  = {m.tenant_id for m in all_keys}

    # Count today's audit events
    today_events = audit_log.get_recent(limit=200)
    import time as _time  # noqa: PLC0415
    today_start = _time.time() - 86400
    audit_today = sum(1 for e in today_events if e.get("timestamp", 0) >= today_start)

    # Build usage list for all keys
    usages = []
    for meta in all_keys:
        usage     = key_store.get_usage(meta.key)
        req_used  = usage["requests"]
        tok_used  = usage["tokens"]
        req_limit = meta.quota_requests
        tok_limit = meta.quota_tokens
        usages.append(ApiKeyUsage(
            key_preview=meta.key[:16] + "…",
            name=meta.name,
            tenant_id=meta.tenant_id,
            role=meta.role,
            requests_used=req_used,
            requests_limit=req_limit,
            requests_remaining=max(0, req_limit - req_used) if req_limit else -1,
            tokens_used=tok_used,
            tokens_limit=tok_limit,
            tokens_remaining=max(0, tok_limit - tok_used) if tok_limit else -1,
            quota_pct_requests=round((req_used / req_limit * 100), 1) if req_limit else 0.0,
            quota_pct_tokens=round((tok_used / tok_limit * 100), 1) if tok_limit else 0.0,
            is_active=meta.is_active,
        ))

    return AdminStatsResponse(
        total_active_keys=len(all_keys),
        total_tenants=len(tenants),
        audit_events_today=audit_today,
        keys=usages,
    )
