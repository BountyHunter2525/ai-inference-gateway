"""
NexusAI Prometheus Metrics Registry
====================================
Single source of truth for all instrumentation counters, histograms, and gauges.

Import `metrics` from this module in any service or endpoint to record observations.
The /api/v1/metrics endpoint reads from this registry and returns the Prometheus
text exposition format.

Metric naming follows Prometheus conventions:
  nexusai_<subsystem>_<name>_<unit>
"""

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ---------------------------------------------------------------------------
# Inference metrics
# ---------------------------------------------------------------------------

INFERENCE_REQUESTS_TOTAL = Counter(
    "nexusai_inference_requests_total",
    "Total number of inference requests received.",
    ["provider", "cache_result"],
    # cache_result: "hit" | "miss" | "volatile_bypass"
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "nexusai_inference_latency_seconds",
    "End-to-end inference latency in seconds.",
    ["provider", "cache_result"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

INFERENCE_TOKENS_TOTAL = Counter(
    "nexusai_inference_tokens_total",
    "Cumulative token usage across all LLM calls.",
    ["provider"],
)

INFERENCE_ERRORS_TOTAL = Counter(
    "nexusai_inference_errors_total",
    "Total inference requests that resulted in an error.",
    ["provider", "error_type"],
)

# ---------------------------------------------------------------------------
# Semantic cache metrics
# ---------------------------------------------------------------------------

CACHE_HITS_TOTAL = Counter(
    "nexusai_cache_hits_total",
    "Cumulative semantic cache hits.",
)

CACHE_MISSES_TOTAL = Counter(
    "nexusai_cache_misses_total",
    "Cumulative semantic cache misses.",
)

CACHE_ENTRIES_GAUGE = Gauge(
    "nexusai_cache_entries",
    "Current number of active cached entries.",
)

CACHE_SIMILARITY_HISTOGRAM = Histogram(
    "nexusai_cache_similarity_score",
    "Distribution of cosine similarity scores on cache lookup.",
    buckets=(0.50, 0.60, 0.70, 0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.97, 0.99, 1.0),
)

CACHE_STORE_LATENCY_SECONDS = Histogram(
    "nexusai_cache_store_latency_seconds",
    "Time taken to embed and persist a new cache entry.",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# ---------------------------------------------------------------------------
# Embedder metrics
# ---------------------------------------------------------------------------

EMBED_LATENCY_SECONDS = Histogram(
    "nexusai_embed_latency_seconds",
    "Time taken by the embedder to encode a single text.",
    ["backend"],  # "sentence_transformers" | "hash_fallback"
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
)

EMBED_REQUESTS_TOTAL = Counter(
    "nexusai_embed_requests_total",
    "Total embedding encode calls.",
    ["backend"],
)

# ---------------------------------------------------------------------------
# Rate limiter metrics
# ---------------------------------------------------------------------------

RATE_LIMIT_ALLOWED_TOTAL = Counter(
    "nexusai_rate_limit_allowed_total",
    "Requests allowed by the sliding-window rate limiter.",
)

RATE_LIMIT_REJECTED_TOTAL = Counter(
    "nexusai_rate_limit_rejected_total",
    "Requests rejected by the sliding-window rate limiter.",
)

# ---------------------------------------------------------------------------
# Volatility classifier metrics
# ---------------------------------------------------------------------------

VOLATILE_QUERIES_TOTAL = Counter(
    "nexusai_volatile_queries_total",
    "Queries classified as volatile / real-time (cache bypassed).",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def prometheus_output() -> tuple[bytes, str]:
    """
    Returns (body_bytes, content_type) ready to be served by the /metrics endpoint.
    Uses the default global REGISTRY which collects all metrics defined above.
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
