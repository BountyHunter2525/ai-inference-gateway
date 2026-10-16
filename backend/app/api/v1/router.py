from fastapi import APIRouter

from app.api.v1.cache_admin import router as cache_router
from app.api.v1.health import router as health_router
from app.api.v1.inference import router as inference_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(inference_router)
api_v1_router.include_router(cache_router)
