import time

from fastapi import APIRouter, Depends, Response

from app.api.deps import verify_api_key
from app.schemas.inference import InferenceRequest, InferenceResponse
from app.services.embedder import embedder_service
from app.services.llm_provider import llm_service
from app.services.query_classifier import is_volatile_query
from app.services.semantic_cache import semantic_cache

router = APIRouter(tags=["Inference"])


@router.post("/infer", response_model=InferenceResponse)
async def infer(
    payload: InferenceRequest,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Main AI Inference Gateway Endpoint.
    1. Checks if query contains real-time/volatile parameters (bypasses cache).
    2. Checks Semantic Cache for existing vectors with cosine similarity >= threshold.
    3. On Cache Hit -> Returns cached response immediately with near-zero latency.
    4. On Cache Miss -> Dispatches inference to selected LLM, stores result in cache with TTL.
    """
    start_time = time.time()

    # 1. Volatility check (e.g. weather, stock price, live events)
    is_volatile, volatile_reason = is_volatile_query(payload.prompt)
    should_bypass_cache = payload.bypass_cache or is_volatile

    prompt_vector = None

    # 2. Check Semantic Cache if not bypassed
    if not should_bypass_cache:
        prompt_vector = embedder_service.embed_text(payload.prompt)
        is_hit, cached_item, similarity = semantic_cache.find_similar(
            prompt=payload.prompt,
            query_vector=prompt_vector
        )

        if is_hit and cached_item:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-Similarity"] = str(similarity)
            response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

            return InferenceResponse(
                prompt=payload.prompt,
                response=cached_item.response,
                model=cached_item.model,
                provider=cached_item.provider,
                cache_hit=True,
                similarity_score=similarity,
                latency_ms=elapsed_ms,
                tokens_used=cached_item.tokens,
                bypassed_due_to_volatility=False
            )

    # 3. Cache Miss or Bypassed: Call LLM Provider
    llm_out, tokens, model_used, provider_used = await llm_service.execute_inference(
        prompt=payload.prompt,
        provider_name=payload.provider,
        model_name=payload.model,
        max_tokens=payload.max_tokens or 256,
        temperature=payload.temperature or 0.7
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

    # 4. Store in Semantic Cache if eligible
    if not should_bypass_cache:
        if prompt_vector is None:
            prompt_vector = embedder_service.embed_text(payload.prompt)

        semantic_cache.store(
            prompt=payload.prompt,
            response=llm_out,
            model=model_used,
            provider=provider_used,
            vector=prompt_vector,
            tokens=tokens,
            ttl_seconds=payload.custom_ttl_seconds
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
        bypassed_due_to_volatility=is_volatile
    )
