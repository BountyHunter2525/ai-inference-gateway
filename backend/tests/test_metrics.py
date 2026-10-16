"""
Unit tests for app/services/metrics.py

Strategy: read the *current* value of each metric before the operation,
perform the operation, then assert the delta. This avoids failures from
cumulative values left by other tests since Prometheus counters are
process-global and never reset.
"""

import pytest
from prometheus_client import REGISTRY


# ── helpers ───────────────────────────────────────────────────────────────────

def _counter_value(metric_name: str, **labels) -> float:
    """Return the current value of a labelled counter from the global registry."""
    try:
        sample_suffix = "_total"
        for metric in REGISTRY.collect():
            if metric.name == metric_name or metric.name == metric_name + sample_suffix:
                for sample in metric.samples:
                    if sample.name.endswith("_total") or sample.name == metric.name:
                        if all(sample.labels.get(k) == v for k, v in labels.items()):
                            return sample.value
        return 0.0
    except Exception:
        return 0.0


def _histogram_count(metric_name: str, **labels) -> float:
    """Return the _count sample value for a labelled histogram."""
    try:
        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    if sample.name.endswith("_count"):
                        if all(sample.labels.get(k) == v for k, v in labels.items()):
                            return sample.value
        return 0.0
    except Exception:
        return 0.0


def _gauge_value(metric_name: str) -> float:
    """Return the current value of an unlabelled gauge."""
    try:
        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    if sample.name == metric_name:
                        return sample.value
        return 0.0
    except Exception:
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Module import & prometheus_output helper
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricsModule:
    def test_import_succeeds(self):
        import app.services.metrics as m  # noqa: F401

    def test_prometheus_output_returns_bytes_and_str(self):
        from app.services.metrics import prometheus_output
        body, content_type = prometheus_output()
        assert isinstance(body, bytes)
        assert isinstance(content_type, str)
        assert "text/plain" in content_type

    def test_prometheus_output_contains_help_lines(self):
        from app.services.metrics import prometheus_output
        body, _ = prometheus_output()
        text = body.decode()
        assert "# HELP" in text
        assert "# TYPE" in text

    def test_prometheus_output_contains_nexusai_metrics(self):
        from app.services.metrics import prometheus_output
        body, _ = prometheus_output()
        text = body.decode()
        assert "nexusai_inference_requests_total" in text
        assert "nexusai_cache_hits_total" in text
        assert "nexusai_embed_requests_total" in text


# ═══════════════════════════════════════════════════════════════════════════════
# Counter increments
# ═══════════════════════════════════════════════════════════════════════════════

class TestCounterIncrements:
    def test_inference_requests_counter_increments(self):
        from app.services.metrics import INFERENCE_REQUESTS_TOTAL
        before = _counter_value("nexusai_inference_requests_total",
                                provider="mock", cache_result="miss")
        INFERENCE_REQUESTS_TOTAL.labels(provider="mock", cache_result="miss").inc()
        after = _counter_value("nexusai_inference_requests_total",
                               provider="mock", cache_result="miss")
        assert after == before + 1

    def test_inference_requests_hit_label(self):
        from app.services.metrics import INFERENCE_REQUESTS_TOTAL
        before = _counter_value("nexusai_inference_requests_total",
                                provider="mock", cache_result="hit")
        INFERENCE_REQUESTS_TOTAL.labels(provider="mock", cache_result="hit").inc()
        after = _counter_value("nexusai_inference_requests_total",
                               provider="mock", cache_result="hit")
        assert after == before + 1

    def test_inference_requests_volatile_label(self):
        from app.services.metrics import INFERENCE_REQUESTS_TOTAL
        before = _counter_value("nexusai_inference_requests_total",
                                provider="mock", cache_result="volatile_bypass")
        INFERENCE_REQUESTS_TOTAL.labels(provider="mock", cache_result="volatile_bypass").inc()
        after = _counter_value("nexusai_inference_requests_total",
                               provider="mock", cache_result="volatile_bypass")
        assert after == before + 1

    def test_tokens_counter_increments_by_amount(self):
        from app.services.metrics import INFERENCE_TOKENS_TOTAL
        before = _counter_value("nexusai_inference_tokens_total", provider="mock")
        INFERENCE_TOKENS_TOTAL.labels(provider="mock").inc(42)
        after = _counter_value("nexusai_inference_tokens_total", provider="mock")
        assert after == before + 42

    def test_errors_counter_increments(self):
        from app.services.metrics import INFERENCE_ERRORS_TOTAL
        before = _counter_value("nexusai_inference_errors_total",
                                provider="mock", error_type="RuntimeError")
        INFERENCE_ERRORS_TOTAL.labels(provider="mock", error_type="RuntimeError").inc()
        after = _counter_value("nexusai_inference_errors_total",
                               provider="mock", error_type="RuntimeError")
        assert after == before + 1

    def test_cache_hits_counter_increments(self):
        from app.services.metrics import CACHE_HITS_TOTAL
        before = _counter_value("nexusai_cache_hits_total")
        CACHE_HITS_TOTAL.inc()
        after = _counter_value("nexusai_cache_hits_total")
        assert after == before + 1

    def test_cache_misses_counter_increments(self):
        from app.services.metrics import CACHE_MISSES_TOTAL
        before = _counter_value("nexusai_cache_misses_total")
        CACHE_MISSES_TOTAL.inc()
        after = _counter_value("nexusai_cache_misses_total")
        assert after == before + 1

    def test_embed_requests_counter_increments(self):
        from app.services.metrics import EMBED_REQUESTS_TOTAL
        before = _counter_value("nexusai_embed_requests_total", backend="hash_fallback")
        EMBED_REQUESTS_TOTAL.labels(backend="hash_fallback").inc()
        after = _counter_value("nexusai_embed_requests_total", backend="hash_fallback")
        assert after == before + 1

    def test_rate_limit_allowed_increments(self):
        from app.services.metrics import RATE_LIMIT_ALLOWED_TOTAL
        before = _counter_value("nexusai_rate_limit_allowed_total")
        RATE_LIMIT_ALLOWED_TOTAL.inc()
        after = _counter_value("nexusai_rate_limit_allowed_total")
        assert after == before + 1

    def test_rate_limit_rejected_increments(self):
        from app.services.metrics import RATE_LIMIT_REJECTED_TOTAL
        before = _counter_value("nexusai_rate_limit_rejected_total")
        RATE_LIMIT_REJECTED_TOTAL.inc()
        after = _counter_value("nexusai_rate_limit_rejected_total")
        assert after == before + 1

    def test_volatile_queries_counter_increments(self):
        from app.services.metrics import VOLATILE_QUERIES_TOTAL
        before = _counter_value("nexusai_volatile_queries_total")
        VOLATILE_QUERIES_TOTAL.inc()
        after = _counter_value("nexusai_volatile_queries_total")
        assert after == before + 1


# ═══════════════════════════════════════════════════════════════════════════════
# Histogram observations
# ═══════════════════════════════════════════════════════════════════════════════

class TestHistogramObservations:
    def test_inference_latency_histogram_records(self):
        from app.services.metrics import INFERENCE_LATENCY_SECONDS
        before = _histogram_count("nexusai_inference_latency_seconds",
                                  provider="mock", cache_result="miss")
        INFERENCE_LATENCY_SECONDS.labels(provider="mock", cache_result="miss").observe(0.123)
        after = _histogram_count("nexusai_inference_latency_seconds",
                                 provider="mock", cache_result="miss")
        assert after == before + 1

    def test_cache_similarity_histogram_records(self):
        from app.services.metrics import CACHE_SIMILARITY_HISTOGRAM
        before = _histogram_count("nexusai_cache_similarity_score")
        CACHE_SIMILARITY_HISTOGRAM.observe(0.95)
        after = _histogram_count("nexusai_cache_similarity_score")
        assert after == before + 1

    def test_cache_store_latency_histogram_records(self):
        from app.services.metrics import CACHE_STORE_LATENCY_SECONDS
        before = _histogram_count("nexusai_cache_store_latency_seconds")
        CACHE_STORE_LATENCY_SECONDS.observe(0.005)
        after = _histogram_count("nexusai_cache_store_latency_seconds")
        assert after == before + 1

    def test_embed_latency_histogram_records(self):
        from app.services.metrics import EMBED_LATENCY_SECONDS
        before = _histogram_count("nexusai_embed_latency_seconds", backend="hash_fallback")
        EMBED_LATENCY_SECONDS.labels(backend="hash_fallback").observe(0.002)
        after = _histogram_count("nexusai_embed_latency_seconds", backend="hash_fallback")
        assert after == before + 1


# ═══════════════════════════════════════════════════════════════════════════════
# Gauge operations
# ═══════════════════════════════════════════════════════════════════════════════

class TestGaugeOperations:
    def test_cache_entries_gauge_set(self):
        from app.services.metrics import CACHE_ENTRIES_GAUGE
        CACHE_ENTRIES_GAUGE.set(10)
        assert _gauge_value("nexusai_cache_entries") == 10.0

    def test_cache_entries_gauge_inc(self):
        from app.services.metrics import CACHE_ENTRIES_GAUGE
        CACHE_ENTRIES_GAUGE.set(0)
        CACHE_ENTRIES_GAUGE.inc()
        assert _gauge_value("nexusai_cache_entries") == 1.0

    def test_cache_entries_gauge_dec(self):
        from app.services.metrics import CACHE_ENTRIES_GAUGE
        CACHE_ENTRIES_GAUGE.set(5)
        CACHE_ENTRIES_GAUGE.dec()
        assert _gauge_value("nexusai_cache_entries") == 4.0
