from typing import Optional

from fastapi import Header, HTTPException, Query, status

from app.config import settings
from app.services.rate_limiter import rate_limiter


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    api_key_query: str | None = Query(None, alias="api_key")
) -> str:
    """
    Validates the provided API key against configured authorized keys.
    Accepts key via X-API-Key header or ?api_key= query param.
    """
    key = x_api_key or api_key_query

    # If no keys are configured, permit in development
    valid_keys = settings.valid_api_keys
    if not valid_keys:
        return "dev-unrestricted"

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide 'X-API-Key' header or 'api_key' query parameter."
        )

    if key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key provided."
        )

    # Check Rate Limit for this key
    allowed, remaining, retry_after = rate_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    return key
