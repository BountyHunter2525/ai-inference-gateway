import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import verify_api_key
from app.schemas.inference import InferenceRequest, InferenceResponse
from app.services.cache_ttl_policy import ttl_policy
from app.services.embedder import embedder_service
from app.services.llm_provider import llm_service
from app.services.metrics import (
    INFERENCE_ERRORS_TOTAL,
    INFERENCE_LATENCY_SECONDS,
    INFERENCE_REQUESTS_TOTAL,
    INFERENCE_TOKENS_TOTAL,
    VOLATILE_QUERIES_TOTAL,
)
from app.services.query_classifier import is_volatile_query
from app.services.semantic_cache import semantic_cache

router = APIRouter(tags=["Inference"])


@router.post("/infer", response_model=InferenceResponse)
async def infer(
    payload: InferenceRequest,
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key),
):
    """
    Main AI Inference Gateway Endpoint.

    Pipeline:
    1. Volatility check — real-time queries bypass cache entirely.
    2. Semantic cache lookup — cosine similarity >= threshold → instant HIT.
    3. LLM dispatch — cache MISS routes to the configured provider.
    4. Adaptive TTL — new entries receive a TTL based on query category
       (factual 24 h, technical 6 h, general 1 h).
    5. Cache store — response + vector persisted with LRU eviction guard.
    """
    start_time = time.time()
    provider_label = (payload.provider or "mock").lower()

    try:
        # ── 1. Volatility check ───────────────────────────────────────────────
        is_volatile, _ = is_volatile_query(payload.prompt)
        if is_volatile:
            VOLATILE_QUERIES_TOTAL.inc()

        should_bypass_cache = payload.bypass_cache or is_volatile
        prompt_vector = None

        # ── 2. Semantic cache lookup ──────────────────────────────────────────
        if not should_bypass_cache:
            prompt_vector = embedder_service.embed_text(payload.prompt)
            is_hit, cached_item, similarity = semantic_cache.find_similar(
                prompt=payload.prompt,
                query_vector=prompt_vector,
            )

            if is_hit and cached_item:
                elapsed_s = time.time() - start_time
                elapsed_ms = round(elapsed_s * 1000, 2)

                INFERENCE_REQUESTS_TOTAL.labels(
                    provider=cached_item.provider, cache_result="hit"
                ).inc()
                INFERENCE_LATENCY_SECONDS.labels(
                    provider=cached_item.provider, cache_result="hit"
                ).observe(elapsed_s)

                # Enterprise: record usage + per-tenant metric
                tenant_id = getattr(request.state, "tenant_id", "default") if hasattr(request, "state") else "default"
                try:
                    from app.services.key_store import key_store as _ks  # noqa: PLC0415
                    from app.services.metrics import ENTERPRISE_REQUESTS_BY_TENANT  # noqa: PLC0415
                    _ks.record_usage(api_key, tokens=cached_item.tokens)
                    ENTERPRISE_REQUESTS_BY_TENANT.labels(tenant_id=tenant_id, cache_result="hit").inc()
                except Exception:
                    pass

                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Similarity"] = str(similarity)
                response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
                response.headers["X-TTL-Category"] = cached_item.ttl_category

                return InferenceResponse(
                    prompt=payload.prompt,
                    response=cached_item.response,
                    model=cached_item.model,
                    provider=cached_item.provider,
                    cache_hit=True,
                    similarity_score=similarity,
                    latency_ms=elapsed_ms,
                    tokens_used=cached_item.tokens,
                    bypassed_due_to_volatility=False,
                    ttl_category=cached_item.ttl_category,
                    tenant_id=tenant_id,
                )

        # ── 3. LLM dispatch ───────────────────────────────────────────────────
        llm_out, tokens, model_used, provider_used = await llm_service.execute_inference(
            prompt=payload.prompt,
            provider_name=payload.provider,
            model_name=payload.model,
            max_tokens=payload.max_tokens or 256,
            temperature=payload.temperature or 0.7,
        )

        elapsed_s = time.time() - start_time
        elapsed_ms = round(elapsed_s * 1000, 2)
        cache_result = "volatile_bypass" if is_volatile else "miss"

        INFERENCE_REQUESTS_TOTAL.labels(provider=provider_used, cache_result=cache_result).inc()
        INFERENCE_LATENCY_SECONDS.labels(provider=provider_used, cache_result=cache_result).observe(elapsed_s)
        INFERENCE_TOKENS_TOTAL.labels(provider=provider_used).inc(tokens)

        # Enterprise: record usage + per-tenant metric
        tenant_id = getattr(request.state, "tenant_id", "default") if hasattr(request, "state") else "default"
        try:
            from app.services.key_store import key_store as _ks  # noqa: PLC0415
            from app.services.metrics import ENTERPRISE_REQUESTS_BY_TENANT  # noqa: PLC0415
            _ks.record_usage(api_key, tokens=tokens)
            ENTERPRISE_REQUESTS_BY_TENANT.labels(tenant_id=tenant_id, cache_result=cache_result).inc()
        except Exception:
            pass

        response.headers["X-Cache"] = "MISS"
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        # ── 4 & 5. Adaptive TTL + cache store ─────────────────────────────────
        ttl_category = "general"
        if not should_bypass_cache:
            if prompt_vector is None:
                prompt_vector = embedder_service.embed_text(payload.prompt)

            # Respect explicit custom_ttl_seconds; otherwise use adaptive policy
            if payload.custom_ttl_seconds:
                ttl_seconds = payload.custom_ttl_seconds
                ttl_category = ttl_policy.category_label(payload.prompt)
            else:
                decision = ttl_policy.decide(payload.prompt)
                ttl_seconds = decision.ttl_seconds
                ttl_category = decision.category

            response.headers["X-TTL-Category"] = ttl_category

            semantic_cache.store(
                prompt=payload.prompt,
                response=llm_out,
                model=model_used,
                provider=provider_used,
                vector=prompt_vector,
                tokens=tokens,
                ttl_seconds=ttl_seconds,
                ttl_category=ttl_category,
            )

        return InferenceResponse(
            prompt=payload.prompt,
            response=llm_out,
            model=model_used,
            provider=provider_used,
            cache_hit=False,
            similarity_score=None,
            latency_ms=elapsed_ms,
            tokens_used=tokens,
            bypassed_due_to_volatility=is_volatile,
            ttl_category=ttl_category if not is_volatile else None,
            tenant_id=tenant_id,
        )

    except HTTPException:
        raise
    except Exception as exc:
        INFERENCE_ERRORS_TOTAL.labels(
            provider=provider_label, error_type=type(exc).__name__
        ).inc()
        raise HTTPException(status_code=502, detail=f"Inference failed: {exc}") from exc
