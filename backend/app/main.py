from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs startup warm-up, then yields to serve traffic."""
    from app.services.cache_warming import startup_warmup  # noqa: PLC0415
    await startup_warmup()
    yield
    # Nothing to clean up on shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Intelligent AI Inference Gateway with Semantic Caching, "
        "Adaptive TTL, LRU Eviction, Cache Warming, "
        "Volatility Classification, and Sliding-Window Rate Limiting."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Cache",
        "X-Cache-Similarity",
        "X-Response-Time-Ms",
        "X-TTL-Category",
        "X-Tenant-ID",
        "X-Quota-Requests-Remaining",
        "X-Quota-Tokens-Remaining",
    ],
)

# Mount API V1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Serve frontend static playground
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit /docs for the API."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
