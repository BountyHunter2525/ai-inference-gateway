"""
FastAPI Dependencies
=====================
verify_api_key  — validates key, enforces daily quota, records audit event,
                  injects tenant context into request state, sets response headers.

Changes from original:
  - Uses KeyStore instead of raw settings.valid_api_keys list
  - Enforces daily QUOTA_DAILY_REQUESTS / QUOTA_DAILY_TOKENS
  - Records every request to the audit log
  - Sets X-Tenant-ID and X-Quota-Remaining response headers
  - Records per-tenant Prometheus counters
"""

import logging

from fastapi import Header, HTTPException, Query, Request, Response, status

from app.config import settings
from app.services.rate_limiter import rate_limiter

# Setup logging
logger = logging.getLogger(__name__)


async def verify_api_key(
    request: Request,
    response: Response,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    api_key_query: str | None = Query(None, alias="api_key"),
) -> str:
    """
    Full enterprise auth dependency.

    Order of checks:
      1. Key present
      2. Key valid & active  (KeyStore)
      3. Sliding-window rate limit
      4. Daily quota (requests + tokens)
      5. Audit log event
      6. Response headers (X-Tenant-ID, X-Quota-Remaining)
    """
    # Late imports to avoid circular imports at module load time
    from app.services import audit_log  # noqa: PLC0415
    from app.services.key_store import key_store  # noqa: PLC0415
    from app.services.metrics import (  # noqa: PLC0415
        ENTERPRISE_AUTH_FAILURES_TOTAL,
        ENTERPRISE_QUOTA_EXCEEDED_TOTAL,
        RATE_LIMIT_ALLOWED_TOTAL,
        RATE_LIMIT_REJECTED_TOTAL,
    )

    key = x_api_key or api_key_query
    endpoint = str(request.url.path)
    method   = request.method

    # ── 1. Key present ────────────────────────────────────────────────────────
    if not key:
        ENTERPRISE_AUTH_FAILURES_TOTAL.labels(reason="missing").inc()
        audit_log.log_event(
            "auth_failed", endpoint=endpoint, method=method,
            status_code=401, detail="Missing API key",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide 'X-API-Key' header or 'api_key' query parameter.",
        )

    # ── 2. Key valid & active ─────────────────────────────────────────────────
    meta = key_store.get_key(key)
    if meta is None:
        # Fall back to legacy config-only keys (backwards compat)
        if key in settings.valid_api_keys:
            tenant_id = "default"
            role      = "user"
        else:
            ENTERPRISE_AUTH_FAILURES_TOTAL.labels(reason="invalid").inc()
            audit_log.log_event(
                "auth_failed", api_key=key, endpoint=endpoint, method=method,
                status_code=403, detail="Invalid or revoked API key",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API Key provided.",
            )
    else:
        tenant_id = meta.tenant_id
        role      = meta.role

    # ── 3. Sliding-window rate limit ──────────────────────────────────────────
    allowed, remaining_rl, retry_after = rate_limiter.is_allowed(key)
    if not allowed:
        RATE_LIMIT_REJECTED_TOTAL.inc()
        audit_log.log_event(
            "auth_failed", api_key=key, tenant_id=tenant_id,
            endpoint=endpoint, method=method,
            status_code=429, detail=f"Rate limit exceeded, retry in {retry_after}s",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    RATE_LIMIT_ALLOWED_TOTAL.inc()

    # ── 4. Daily quota ────────────────────────────────────────────────────────
    if meta is not None:
        within_quota, quota_info = key_store.check_quota(key)
        if not within_quota:
            ENTERPRISE_QUOTA_EXCEEDED_TOTAL.labels(tenant_id=tenant_id).inc()
            audit_log.log_event(
                "quota_exceeded", api_key=key, tenant_id=tenant_id,
                endpoint=endpoint, method=method,
                status_code=429,
                detail=(
                    f"Daily quota exhausted: "
                    f"{quota_info.get('requests_used')}/{quota_info.get('requests_limit')} requests, "
                    f"{quota_info.get('tokens_used')}/{quota_info.get('tokens_limit')} tokens"
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily usage quota exceeded. Quota resets at midnight UTC.",
                headers={"X-Quota-Reset": "midnight UTC"},
            )

        # Set quota headers for the client
        req_rem = quota_info.get("requests_remaining", -1)
        tok_rem = quota_info.get("tokens_remaining", -1)
        response.headers["X-Quota-Requests-Remaining"] = str(req_rem) if req_rem >= 0 else "unlimited"
        response.headers["X-Quota-Tokens-Remaining"]   = str(tok_rem) if tok_rem >= 0 else "unlimited"

    # ── 5. Inject tenant context into request state ───────────────────────────
    request.state.tenant_id = tenant_id
    request.state.api_key   = key
    request.state.role      = role

    # ── 6. Response headers ───────────────────────────────────────────────────
    response.headers["X-Tenant-ID"] = tenant_id

    # ── 7. Audit the request ──────────────────────────────────────────────────
    audit_log.log_event(
        "inference" if endpoint.endswith("/infer") else "api_request",
        api_key=key, tenant_id=tenant_id,
        endpoint=endpoint, method=method,
        status_code=200,
    )

    return key


async def verify_admin_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    api_key_query: str | None = Query(None, alias="api_key"),
) -> str:
    """
    Stricter dependency for /admin/* endpoints.
    Accepts only the configured ADMIN_API_KEY or any key with role='admin'.
    """
    from app.services import audit_log  # noqa: PLC0415
    from app.services.key_store import key_store  # noqa: PLC0415
    from app.services.metrics import ENTERPRISE_AUTH_FAILURES_TOTAL  # noqa: PLC0415

    key = x_api_key or api_key_query
    if not key:
        ENTERPRISE_AUTH_FAILURES_TOTAL.labels(reason="missing").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin endpoint requires an API key with admin role.",
        )

    # Accept the master admin key directly
    if key == settings.ADMIN_API_KEY:
        return key

    # Or any registered key with role='admin'
    meta = key_store.get_key(key)
    if meta and meta.role == "admin" and meta.is_active:
        return key

    ENTERPRISE_AUTH_FAILURES_TOTAL.labels(reason="invalid").inc()
    audit_log.log_event(
        "auth_failed", api_key=key, endpoint="/admin",
        status_code=403, detail="Insufficient privileges for admin endpoint",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access denied. Requires admin role.",
    )
