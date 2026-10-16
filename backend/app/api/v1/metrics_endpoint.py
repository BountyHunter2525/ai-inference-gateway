"""
GET /api/v1/metrics
-------------------
Prometheus text-format scrape endpoint.

The endpoint is intentionally open (no API-key guard) so that a Prometheus
server running in a separate container can scrape it without needing a
credential.  If your deployment requires auth, add `Depends(verify_api_key)`.

Response headers:
  Content-Type: text/plain; version=0.0.4; charset=utf-8
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.services.metrics import prometheus_output

router = APIRouter(tags=["Observability"])


@router.get("/metrics", include_in_schema=True)
async def prometheus_metrics():
    """
    Exposes all NexusAI Prometheus metrics in the standard text exposition
    format (version 0.0.4).  Point your Prometheus scrape config here.

    **Example scrape config:**
    ```yaml
    scrape_configs:
      - job_name: nexusai
        static_configs:
          - targets: ['gateway:8000']
        metrics_path: /api/v1/metrics
    ```
    """
    body, content_type = prometheus_output()
    return Response(content=body, media_type=content_type)
