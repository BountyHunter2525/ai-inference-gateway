from fastapi import APIRouter
from app.config import settings
from app.schemas.inference import HealthResponse
from app.services.semantic_cache import semantic_cache
from app.services.embedder import _model_failed

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Gateway health and diagnostic check.
    """
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        backend_storage=semantic_cache.backend_type,
        default_provider=settings.DEFAULT_LLM_PROVIDER,
        embedder_ready=not _model_failed
    )
